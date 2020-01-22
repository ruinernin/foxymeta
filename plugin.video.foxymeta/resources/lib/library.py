import errno
import json
import os
import shutil
import time
from xml.dom import minidom
from xml.etree import ElementTree

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
        

def clean_library(_type):
    """Remove all `_type` ('Movies', 'TV') library files."""
    libdir = '{}/Library/{}/'.format(router.addon_data_dir, _type)
    if not os.path.exists(libdir):
        return
    for _dir in os.listdir(libdir):
        shutil.rmtree(libdir + _dir)
    xbmc.executebuiltin('CleanLibrary(video)', wait=True)
    

def add_sources():
    sources = xbmc.translatePath('special://userdata/sources.xml')
    tv_lib = router.addon_data_dir + '/Library/TV/'
    movie_lib = router.addon_data_dir + '/Library/Movies/'
    tree = ElementTree.parse(sources)
    root = tree.getroot()
    video = root.find('video')
    paths = [source.find('path').text for source in video.findall('source')]
    updated = False
    for lib, _name in ((movie_lib, 'Movies'), (tv_lib, 'TV')):
        if lib not in paths:
            source = ElementTree.SubElement(video, 'source')
            name = ElementTree.SubElement(source, 'name')
            name.text = "FoxyMeta " + _name
            path = ElementTree.SubElement(source, 'path',
                                                    pathversion='1')
            path.text = lib
            updated = True
    if updated:
        tree.write(sources)


def library_imdbids():
    """Return a list of movie imdbids existing in library."""
    result = jsonrpc.get_movies(properties=['imdbnumber'])
    return [movie['imdbnumber'] for movie in result.get('movies', list())]


def library_shows_tvdbid():
    """Return a list of shows in library mapped by tvdbid to library id."""
    result = jsonrpc.get_shows(properties=['uniqueid'])
    return {int(show['uniqueid']['tvdb']): show['tvshowid']
            for show in result.get('tvshows', list()) if 'tvdb' in show['uniqueid']}


def library_episodes(tvshowid):
    """Return a list of tuples of episodes that exist for tvshowid."""
    result = jsonrpc.get_episodes(tvshowid, properties=['episode', 'season'])
    return [(episode['season'], episode['episode'])
            for episode in result['episodes']]


def imdb_nfo(movie, tag):
    imdbid = movie['movie']['ids']['imdb']
    imdb_str = 'http://www.imdb.com/title/{}/'.format(imdbid)
    
    movie_root = ElementTree.Element('movie')
    dateadded_node = ElementTree.SubElement(movie_root, 'dateadded')
    dateadded_node.text = movie.get('listed_at', '')
    
    ratings_node = ElementTree.SubElement(movie_root, 'ratings')
    imdb_node = ElementTree.SubElement(ratings_node, 'rating')
    imdb_node.attrib = {'name': 'imdb', 'max': '10'}
    imdb_value = ElementTree.SubElement(imdb_node, 'value')
    imdb_value.text = str(movie['movie'].get('rating', ''))
    imdb_votes = ElementTree.SubElement(imdb_node, 'votes')
    imdb_votes.text = str(movie['movie'].get('votes', ''))
    
    outline_node = ElementTree.SubElement(movie_root, 'plot')
    outline_node.text = movie['movie'].get('overview', '')
    mpaa_node = ElementTree.SubElement(movie_root, 'mpaa')
    mpaa_node.text = movie['movie'].get('certification', '')
    premiered_node = ElementTree.SubElement(movie_root, 'premiered')
    premiered_node.text = movie['movie'].get('released', '')
    
    # crashes in this block with Nausicaa
    for tag in ['title', 'tagline', 'runtime', 'country', 'director', 'year',
                'trailer']:
        tag_node = ElementTree.SubElement(movie_root, tag)
        tag_node.text = u'{}'.format(movie['movie'].get(tag, ''))
    
    for id in movie['movie']['ids']:
        id_node = ElementTree.SubElement(movie_root, 'uniqueid')
        id_node.attrib = {'type': id, 'default': 'true' if id == 'imdb' else 'false'}
        id_node.text = u'{}'.format(movie['movie']['ids'][id])
        
    for genre in movie['movie']['genres']:
        genre_node = ElementTree.SubElement(movie_root, 'genre')
        genre_node.text = u'{}'.format(genre.capitalize())
    
    if tag:
        tag_node = ElementTree.SubElement(movie_root, 'tag')
        tag_node.text = u'{}'.format(tag)
    
    xml = ElementTree.tostring(movie_root)
    new_xml = minidom.parseString(xml).toprettyxml(indent='    ')
    nfo_str = new_xml + '\n\n' + imdb_str
            
    return nfo_str


def tvdb_nfo(tvdbid):
    tvdb_str = 'http://thetvdb.com/?tab=series&id={}'.format(tvdbid)
    
    return tvdb_str
    
    
def create_trakt_playlist(user, slug, type):
    playlist_path = xbmc.translatePath('special://profile/playlists/video')
    _list = metadata.trakt_list(user, slug, type, items=False)
    
    sort_by_values = (('rank', 'top250'), ('added', 'dateadded'),
                      ('title', 'sorttitle'), ('released', ''),
                      ('runtime', 'time'), ('popularity', 'playcount'),
                      ('percentage', 'rating'), ('votes', 'votes'),
                      ('my_rating', 'userrating'), ('random', 'random'), )
    sort_by_translation = {tag: val for tag, val in sort_by_values}
                      
    info = {'type': type,
            'username': _list['user']['username'],
            'name': '{} {}'.format(_list['name'], type.capitalize()),
            'sort_how': _list['sort_how'] + 'ending'}
    
    if _list['sort_by'] in sort_by_translation:
        info.update({'sort_by': sort_by_translation[_list['sort_by']]})
    
    playlist_root = ElementTree.Element('smartplaylist')
    playlist_root.set('type', info['type'])
    
    name_node = ElementTree.SubElement(playlist_root, 'name')
    name_node.text = '{} by {}'.format(info['name'], info['username'])
    
    match_node = ElementTree.SubElement(playlist_root, 'match')
    match_node.text = 'all'
    rule_node = ElementTree.SubElement(playlist_root, 'rule')
    rule_node.attrib = {'field': 'tag', 'operator': 'is'}
    
    value_node = ElementTree.SubElement(rule_node, 'value')
    value_node.text = slug
    order_node = ElementTree.SubElement(playlist_root, 'order')
    order_node.attrib = {'direction': info['sort_how']}
    order_node.text = info['sort_by']
    
    xml = ElementTree.tostring(playlist_root, 'utf-8')
    new_xml = minidom.parseString(xml).toprettyxml(indent='    ')
    
    with open(os.path.join(playlist_path, '{}.xsp'.format(info['name'])), 'w') as xsp:
        xsp.write(new_xml)

    
@router.route('/library/add/movie')
def create_movie(movie, tag=''):
    imdbid = movie['movie']['ids']['imdb']
    movie_dir = '{}/Library/Movies/{}'.format(router.addon_data_dir, imdbid)
    if not mkdir(movie_dir):
        return
    with open('{}/{}.nfo'.format(movie_dir, imdbid), 'w') as nfo:
        nfo.write(imdb_nfo(movie, tag).encode('utf-8'))
    with open('{}/{}.strm'.format(movie_dir, imdbid), 'w') as strm:
        strm.write(router.build_url(player.play_movie,
                                    get_metadata=False,
                                    **movie['movie']['ids']))


@router.route('/library/add/show')
def create_show(ids, tag=''):
    tvdbid = ids['tvdb']
    show_dir = '{}/Library/TV/{}'.format(router.addon_data_dir, tvdbid)
    if not mkdir(show_dir):
        return
    with open('{}/tvshow.nfo'.format(show_dir), 'w') as nfo:
        if tag:
            show_root = ElementTree.Element('tvshow')
            tag_node = ElementTree.SubElement(show_root, 'tag')
            tag_node.text = tag
            xml = ElementTree.tostring(show_root, 'utf-8')
            new_xml = minidom.parseString(xml).toprettyxml(indent='    ')
            nfo.write(new_xml)
    
        nfo.write(tvdb_nfo(tvdbid))


@router.route('/library/add/episode')
def create_episode(ids, name, season, episode, tag=''):
    tvdbid = ids['tvdb']
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


@router.route('/library/sync/lists/choose')
def choose_lists():
    trakt_username = router.addon.getSettingString('trakt.username')
    old_choices = router.addon.getSettingString('library.sync.chosen_lists').split(',')
    slugs = []
    names = []
    preselect = []
    chosen_slugs = []
    options = []
    
    lists = []
    lists.extend([metadata.trakt_personal_lists()])
    xbmc.log('personal: {}'.format(lists))
    lists.extend([metadata.trakt_liked_lists(all=True)])
    xbmc.log('all: {}'.format(lists))
    
    for list in lists[0]:
        slug ='{}.{}'.format(list['ids']['slug'], list['user']['ids']['slug'])
        name = list['name']
        username = list['user']['username']
        description = list['description']
        slugs.append(slug)
        names.append(name)
        
        item = xbmcgui.ListItem(name)
        options.append(item)
    
    for page in lists[1]:
        for list in page:
            list = list['list']
        
            slug ='{}.{}'.format(list['ids']['slug'], list['user']['ids']['slug'])
            name = list['name']
            username = list['user']['username']
            liked_title = '{} by {}'.format(name, username)
            description = list['description']
            slugs.append(slug)
            names.append(name)
            
            item = xbmcgui.ListItem(liked_title)
            options.append(item)

    for slug in slugs:
        if slug in old_choices:
            preselect.append(slugs.index(slug))
    
    choices = xbmcgui.Dialog().multiselect('Choose Lists to Sync', options=options,
                                           preselect=preselect)

    if choices:
        for index in choices:
            chosen_slugs.append(slugs[index])
    
        router.addon.setSettingString('library.sync.chosen_lists', ','.join(chosen_slugs))


@router.route('/library/sync/movies/collection')
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
            create_movie(movie, tag='collection')
            if i % 10 == 0:
                progress.update(int((float(i) / len(movies)) * 100))
    finally:
        progress.close()
        
    router.addon.setSettingString('trakt.last_sync_movies_collection',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)
    
    
@router.route('/library/sync/movies/lists')
def sync_movie_lists(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding Movie Lists to Foxy Library')
    if refresh:
        clean_library('Movies')
    
    chosen_slugs = router.addon.getSettingString('library.sync.chosen_lists').split(',')
    
    in_library = library_imdbids()
    
    for i, chosen in enumerate(chosen_slugs):
        slug, user = chosen.split('.')
        list = metadata.trakt_list(user, slug, 'movies')
        for movie in list:
            imdbid = movie['movie']['ids']['imdb']
            if imdbid in in_library:
                continue
            create_movie(movie, tag=slug)
        
        create_trakt_playlist(user, slug, 'movies')
        progress.update(int((float(i) / len(chosen_slugs)) * 100))
    progress.close()
    
    router.addon.setSettingString('trakt.last_sync_movies_lists',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)
    
    
@router.route('/library/sync/movies/watchlist')
def sync_movie_watchlist(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding Watchlist Movies to Foxy Library')
    if refresh:
        clean_library('Movies')
    movies = metadata.trakt_watchlist(_type='movies')
    in_library = library_imdbids()
    for i, movie in enumerate(movies):
        imdbid = movie['movie']['ids']['imdb']
        if imdbid in in_library:
            continue
        create_movie(movie, tag='watchlist')
        if i % 10 == 0:
            progress.update(int((float(i) / len(movies)) * 100))
    progress.close()
    
    router.addon.setSettingString('trakt.last_sync_movies_watchlist',
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


@router.route('/library/sync/tv/collection')
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
            create_show(ids, tag='collection')
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
        router.addon.setSettingString('trakt.last_sync_tv_collection',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    finally:
        progress.close()
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)
    
    
@router.route('/library/sync/tv/lists')
def sync_tv_lists(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding TV Show Lists to Foxy Library')
    if refresh:
        clean_library('TV')
    
    chosen_slugs = router.addon.getSettingString('library.sync.chosen_lists').split(',')
    
    in_library = library_shows_tvdbid()
    
    for i, chosen in enumerate(chosen_slugs):
        slug, user = chosen.split('.')
        list = metadata.trakt_list(user, slug, 'shows')
        for show in list:
            ids = show['show']['ids']
            tvdbid = ids['tvdb']
            name = show['show']['title']
            create_show(ids, tag=slug)
            try:
                have_episodes = library_episodes(in_library[tvdbid])
            except KeyError:
                have_episodes = ()
            for season in metadata.tvdb_show(tvdbid)['airedSeasons']:
                if season == '0':
                    continue
                for episode in metadata.tvdb_season(tvdbid, season):
                    ep_num = episode['airedEpisodeNumber']
                    if (int(season), int(ep_num)) in have_episodes:
                        continue
                    create_episode(ids, name, season, ep_num)
            create_trakt_playlist(user, slug, 'shows')
            create_trakt_playlist(user, slug, 'episodes')
        progress.update(int((float(i) / len(chosen_slugs)) * 100))
    progress.close()
    
    router.addon.setSettingString('trakt.last_sync_tv_lists',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)

    
@router.route('/library/sync/tv/watchlist')
def sync_show_watchlist(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding Watchlist TV Shows to Foxy Library')
    if refresh:
        clean_library('TV')
    shows = metadata.trakt_watchlist(_type='shows')
    in_library = library_shows_tvdbid()
    for i, show in enumerate(shows):
        ids = show['show']['ids']
        tvdbid = ids['tvdb']
        name = show['show']['title']
        create_show(ids, tag='watchlist')
        try:
            have_episodes = library_episodes(in_library[tvdbid])
        except KeyError:
            have_episodes = ()
        for season in metadata.tvdb_show(tvdbid)['airedSeasons']:
            if season == '0':
                continue
            for episode in metadata.tvdb_season(tvdbid, season):
                ep_num = episode['airedEpisodeNumber']
                if (int(season), int(ep_num)) in have_episodes:
                    continue
                create_episode(ids, name, season, ep_num)
        progress.update(int((float(i) / len(shows)) * 100))
    progress.close()
    
    router.addon.setSettingString('trakt.last_sync_tv_watchlist',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)
