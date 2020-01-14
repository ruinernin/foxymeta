import errno
import json
import os
import shutil
import time
import xml.etree.ElementTree

import xbmc
import xbmcgui

from . import player
from . import jsonrpc
from . import metadata
from .router import router


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EEXIST:
            pass
        else:
            raise
    else:
        return True


def add_sources():
    sources = xbmc.translatePath('special://userdata/sources.xml')
    tv_lib = router.addon_data_dir + '/Library/TV/'
    movie_lib = router.addon_data_dir + '/Library/Movies/'
    tree = xml.etree.ElementTree.parse(sources)
    root = tree.getroot()
    video = root.find('video')
    paths = [source.find('path').text for source in video.findall('source')]
    updated = False
    for lib, _name in ((movie_lib, 'Movies'), (tv_lib, 'TV')):
        if lib not in paths:
            source = xml.etree.ElementTree.SubElement(video, 'source')
            name = xml.etree.ElementTree.SubElement(source, 'name')
            name.text = "FoxyMeta " + _name
            path = xml.etree.ElementTree.SubElement(source, 'path',
                                                    pathversion='1')
            path.text = lib
            updated = True
    if updated:
        tree.write(sources)


def imdb_nfo(imdbid):
    return 'http://www.imdb.com/title/{}/'.format(imdbid)


def tvdb_nfo(tvdbid):
    return 'http://thetvdb.com/?tab=series&id={}'.format(tvdbid)


def create_movie(ids):
    imdbid = ids['imdb']
    movie_dir = '{}/Library/Movies/{}'.format(router.addon_data_dir, imdbid)
    if not mkdir(movie_dir):
        return
    with open('{}/{}.nfo'.format(movie_dir, imdbid), 'w') as nfo:
        nfo.write(imdb_nfo(imdbid))
    with open('{}/{}.strm'.format(movie_dir, imdbid), 'w') as strm:
        strm.write(router.build_url(player.play_movie,
                                    get_metadata=False,
                                    **ids))


def clean_library(_type):
    """Remove all `_type` ('Movies', 'TV') library files."""
    libdir = '{}/Library/{}/'.format(router.addon_data_dir, _type)
    if not os.path.exists(libdir):
        return
    for _dir in os.listdir(libdir):
        shutil.rmtree(libdir + _dir)
    xbmc.executebuiltin('CleanLibrary(video)', wait=True)


def create_show(tvdbid):
    show_dir = '{}/Library/TV/{}'.format(router.addon_data_dir, tvdbid)
    if not mkdir(show_dir):
        return
    with open('{}/tvshow.nfo'.format(show_dir), 'w') as nfo:
        nfo.write(tvdb_nfo(tvdbid))


def create_episode(tvdbid, name, season, episode):
    season_dir = '{}/Library/TV/{}/Season {}'.format(router.addon_data_dir,
                                                     tvdbid,
                                                     season)
    mkdir(season_dir)
    ep_file = '{}/{} - S{:02d}E{:02d}.strm'.format(season_dir,
                                                   name,
                                                   int(season),
                                                   int(episode))
    if os.path.exists(ep_file):
        return
    with open(ep_file, 'w') as strm:
        strm.write(router.build_url(player.play_episode,
                                    _id=tvdbid,
                                    season=season,
                                    episode=episode))


def library_imdbids():
    """Return a list of movie imdbids existing in library."""
    result = jsonrpc.get_movies(properties=['imdbnumber'])
    return [movie['imdbnumber'] for movie in result.get('movies', list())]


def library_shows_tvdbid():
    """Return a list of shows in library mapped by tvdbid to library id."""
    result = jsonrpc.get_shows(properties=['uniqueid'])
    return {int(show['uniqueid']['tvdb']): show['tvshowid']
            for show in result.get('tvshows', list())}


def library_episodes(tvshowid):
    """Return a list of tuples of episodes that exist for tvshowid."""
    result = jsonrpc.get_episodes(tvshowid, properties=['episode', 'season'])
    return [(episode['season'], episode['episode'])
            for episode in result['episodes']]


@router.route('/library/sync/movies')
def sync_movie_collection(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding Movies to Foxy Library')
    try:
        if refresh:
            clean_library('Movies')
        movies = metadata.trakt_collection(_type='movies')
        in_library = library_imdbids()
        for i, movie in enumerate(movies):
            imdbid = movie['movie']['ids']['imdb']
            if imdbid in in_library:
                continue
            create_movie(movie['movie']['ids'])
            if i % 10 == 0:
                progress.update(int((float(i) / len(movies)) * 100))
    finally:
        progress.close()
    router.addon.setSettingString('trakt.last_sync_movies',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)


def aired_since():
    future_checks = json.loads(router.addon.getSetting(
        'library.sync.traktcollection.tv.future_checks'))
    future_checks = {int(k): v for k, v in future_checks.items()}
    aired = [_id for _id, ts in future_checks.items() if ts < time.time()]
    for _id in aired:
        del future_checks[_id]
    router.addon.setSetting('library.sync.traktcollection.tv.future_checks',
                            json.dumps(future_checks))
    return aired


def future_check(tvdbid, epoch):
    future_checks = json.loads(router.addon.getSetting(
        'library.sync.traktcollection.tv.future_checks'))
    future_checks[tvdbid] = epoch
    router.addon.setSetting('library.sync.traktcollection.tv.future_checks',
                            json.dumps(future_checks))


@router.route('/library/sync/tv')
def sync_show_collection(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding TV Shows to Foxy Library')
    try:
        lastupdate = router.addon.getSettingInt(
            'library.sync.traktcollection.tv.lastupdate')
        updates = None
        if refresh:
            clean_library('TV')
        else:
            if (time.time() - lastupdate) < (3600 * 24 * 7):
                updates = [show['id']
                           for show in metadata.tvdb_updates(lastupdate)]
                updates.extend(aired_since())
            else:
                refresh = True
        shows = metadata.trakt_collection(_type='shows')
        in_library = library_shows_tvdbid()
        for i, show in enumerate(shows):
            tvdbid = show['show']['ids']['tvdb']
            name = show['show']['title']
            if not refresh:
                if (tvdbid in in_library) and (tvdbid not in updates):
                    continue
            create_show(tvdbid)
            try:
                have_episodes = library_episodes(in_library[tvdbid])
            except KeyError:
                have_episodes = ()
            for season in metadata.tvdb_show(tvdbid)['airedSeasons']:
                if season == '0':
                    continue
                for episode in metadata.tvdb_season(tvdbid, season):
                    ep_num = episode['airedEpisodeNumber']
                    if 'firstAired' in episode:
                        air_date = metadata.tvdb_airdate_epoch(
                            episode['firstAired']
                        )
                        if air_date > time.time():
                            break
                    else:
                        air_date = None
                        break
                    if (int(season), int(ep_num)) in have_episodes:
                        continue
                    create_episode(tvdbid, name, season, ep_num)
                else:
                    continue
                # Found unaired episodes, save the future air date to recheck
                # on. If there is none rely on updates.
                if air_date:
                    future_check(tvdbid, air_date)
                break
            progress.update(int((float(i) / len(shows)) * 100))
        router.addon.setSettingInt('library.sync.traktcollection.tv.lastupdate',
                                   int(time.time()))
    finally:
        progress.close()
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)
