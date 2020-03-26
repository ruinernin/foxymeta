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
from . import utils
from .router import router


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
    if not os.path.exists(sources):
        return
    
    utils.mkdir(xbmc.translatePath(tv_lib))
    utils.mkdir(xbmc.translatePath(movie_lib))
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
            allowsharing = ElementTree.SubElement(source, 'allowsharing')
            allowsharing.text = 'true'
            updated = True
    if updated:
        xml = ElementTree.tostring(root)
        new_xml = minidom.parseString(xml).toprettyxml(indent='    ')
        with open(sources, 'w') as f:
            f.write(new_xml.encode('utf-8'))


def create_nfo(item, library_tag='', type=''):
    if not type:
        _type = item['type']
    else:
        _type = type
    
    if 'ids' in item:
        ids = item['ids']
    else:
        ids = item[_type]['ids']
        
    _id = ids['imdb' if _type == 'movie' else 'tvdb']
    
    url_str = 'http://www.imdb.com/title/{}/'.format(_id) if _type == 'movie' else 'http://thetvdb.com/?tab=series&id={}'.format(_id)
    
    root = ElementTree.Element('movie' if _type == 'movie' else 'tvshow')
    dateadded_node = ElementTree.SubElement(root, 'dateadded')
    dateadded_node.text = item.get('listed_at', '')
    
    item = item[_type] if _type in item else item
    
    ratings_node = ElementTree.SubElement(root, 'ratings')
    imdb_node = ElementTree.SubElement(ratings_node, 'rating')
    imdb_node.attrib = {'name': 'imdb', 'max': '10'}
    imdb_value = ElementTree.SubElement(imdb_node, 'value')
    imdb_value.text = u'{}'.format(item.get('rating', ''))
    imdb_votes = ElementTree.SubElement(imdb_node, 'votes')
    imdb_votes.text = u'{}'.format(item.get('votes', ''))
    
    outline_node = ElementTree.SubElement(root, 'plot')
    outline_node.text = item.get('overview', '')
    mpaa_node = ElementTree.SubElement(root, 'mpaa')
    mpaa_node.text = item.get('certification', '')
    premiered_node = ElementTree.SubElement(root, 'premiered')
    premiered_node.text = item.get('release' if _type == 'movie' else 'first_aired', '')
    
    if _type == 'show':
        studio_node = ElementTree.SubElement(root, 'studio')
        studio_node.text = item.get('network', '')
        episode_node = ElementTree.SubElement(root, 'episode')
        episode_node.text = u'{}'.format(item.get('aired_episodes', ''))
    
    for tag in ['title', 'tagline', 'runtime', 'country', 'director', 'year',
                'trailer', 'status']:
        tag_node = ElementTree.SubElement(root, tag)
        tag_node.text = u'{}'.format(item.get(tag, ''))
    
    for genre in item.get('genres', []):
        genre_node = ElementTree.SubElement(root, 'genre')
        genre_node.text = u'{}'.format(genre.capitalize())
        
    if library_tag:
        tag_node = ElementTree.SubElement(root, 'tag')
        tag_node.text = u'{}'.format(library_tag)
    
    xml = ElementTree.tostring(root)
    new_xml = minidom.parseString(xml).toprettyxml(indent='    ')
    nfo_str = new_xml + '\n\n' + url_str
            
    return nfo_str
    
    
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
    playlist_root.set('type', 'movies' if info['type'] == 'movies' else 'tvshows')
    
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
    
    filename = utils.get_valid_filename('{}.xsp'.format(info['name']))
    
    with open(os.path.join(playlist_path, filename), 'w') as xsp:
        xsp.write(new_xml)
        
        
@router.route('/library/add/context')
def add_from_context(dbid, dbtype):
    status = 'Already in'
    if dbtype == 'movie':
        in_library = jsonrpc.library_imdbids()
        movie = metadata.trakt_movie(dbid)
        if create_movie(movie, in_library, 'context'):
            status = 'Added to'
        xbmcgui.Dialog().notification('FoxyMeta', '{} ({}) {} Library'
                                                  .format(movie['title'],
                                                          movie['year'],
                                                          status))
    elif dbtype == 'tvshow':
        in_library = jsonrpc.library_shows_tvdbid()
        show = metadata.trakt_show(dbid)
        if create_show(show, in_library, 'context'):
            status = 'Added to'
        xbmcgui.Dialog().notification('FoxyMeta', '{} ({}) {} Library'
                                                  .format(show['title'],
                                                          show['year'],
                                                          status))

    
@router.route('/library/add/movie')
def create_movie(movie, in_library, tag=''):
    if 'ids' in movie:
        ids = movie['ids']
    else:
        ids = movie['movie']['ids']
        
    imdbid = ids['imdb']
    if imdbid in in_library:
        return
    
    movie_dir = '{}/Library/Movies/{}'.format(router.addon_data_dir, imdbid)
    if not utils.mkdir(movie_dir):
        return
    with open('{}/{}.nfo'.format(movie_dir, imdbid), 'w') as nfo:
        nfo.write(create_nfo(movie, tag, 'movie').encode('utf-8'))
    with open('{}/{}.strm'.format(movie_dir, imdbid), 'w') as strm:
        strm.write(router.build_url(player.play_movie,
                                    get_metadata=False,
                                    **ids))
    
    return True


@router.route('/library/add/show')
def create_show(show, in_library, tag=''):
    if 'ids' in show:
        ids = show['ids']
        name = show['title']
    else:
        ids = show['show']['ids']
        name = show['show']['title']
        
    tvdbid = ids['tvdb']
    
    if tvdbid in in_library:
        return
    
    show_dir = '{}/Library/TV/{}'.format(router.addon_data_dir, tvdbid)
    if not utils.mkdir(show_dir):
        return
    with open('{}/tvshow.nfo'.format(show_dir), 'w') as nfo:
        nfo.write(create_nfo(show, tag, 'show').encode('utf-8'))
    
    try:
        have_episodes = jsonrpc.library_episodes(in_library[tvdbid])
    except KeyError:
        have_episodes = ()
        
    tvdbshow = metadata.tvdb_show(tvdbid)
    if tvdbshow:
        for season in tvdbshow.get('airedSeasons', []):
            if season == '0':
                continue
            
            tvdbseason = metadata.tvdb_season(tvdbid, season)
            if tvdbseason:
                for episode in tvdbseason:
                    ep_num = episode['airedEpisodeNumber']
                    if 'firstAired' in episode:
                        first_aired = episode.get('firstAired', None)
                        if first_aired:
                            air_date = metadata.tvdb_airdate_epoch(first_aired) 
                            if air_date > time.time():
                                break
                        else:
                            air_date = None
                            break
                    else:
                        air_date = None
                        break
                    if (int(season), int(ep_num)) in have_episodes:
                        continue
                    create_episode(ids, name, season, ep_num, tag)
                else:
                    continue
                # Found unaired episodes, save the future air date to recheck
                # on. If there is none rely on updates.
                if air_date:
                    future_check(tvdbid, air_date)
                break
    
        return True


@router.route('/library/add/episode')
def create_episode(ids, name, season, episode, tag=''):
    tvdbid = ids['tvdb']
    season_dir = '{}/Library/TV/{}/Season {}'.format(router.addon_data_dir,
                                                     tvdbid,
                                                     season)
    if not utils.mkdir(season_dir):
        return
        
    filename = utils.get_valid_filename(u'{} - S{:02d}E{:02d}.strm'.format(name,
                                                                    int(season),
                                                                    int(episode)))
    ep_file = '{}/{}'.format(season_dir, filename)
    if os.path.exists(ep_file):
        return
    with open(ep_file, 'w') as strm:
        strm.write(router.build_url(player.play_episode,
                                    _id=tvdbid,
                                    season=season,
                                    episode=episode))
                                    
    return True


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
        movies = metadata.trakt_collection(_type='movies', extended=True)
        in_library = jsonrpc.library_imdbids()
        for i, movie in enumerate(movies):
            imdbid = movie['movie']['ids']['imdb']
            create_movie(movie, in_library, 'collection')
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
    try:
        if refresh:
            clean_library('Movies')
        
        chosen_slugs = router.addon.getSettingString('library.sync.chosen_lists').split(',')
        
        in_library = jsonrpc.library_imdbids()
        
        for i, chosen in enumerate(chosen_slugs):
            slug, user = chosen.split('.')
            list = metadata.trakt_list(user, slug, 'movies')
            for movie in list:
                imdbid = movie['movie']['ids']['imdb']
                create_movie(movie, in_library, slug)
            
            create_trakt_playlist(user, slug, 'movies')
            progress.update(int((float(i) / len(chosen_slugs)) * 100))
    finally:
        progress.close()
    
    router.addon.setSettingString('trakt.last_sync_movies_lists',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)
    
    
@router.route('/library/sync/movies/watchlist')
def sync_movie_watchlist(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding Watchlist Movies to Foxy Library')
    try:
        if refresh:
            clean_library('Movies')
        movies = metadata.trakt_watchlist(_type='movies', extended=True)
        in_library = jsonrpc.library_imdbids()
        for i, movie in enumerate(movies):
            imdbid = movie['movie']['ids']['imdb']
            create_movie(movie, in_library, 'watchlist')
            
            progress.update(int((float(i) / len(movies)) * 100))
    finally:
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
        shows = metadata.trakt_collection(_type='shows', extended=True)
        in_library = jsonrpc.library_shows_tvdbid()
        for i, show in enumerate(shows):
            tvdbid = show['show']['ids']['tvdb']
            if not refresh:
                if tvdbid not in updates:
                    continue
            create_show(show, in_library, 'collection')
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
        
        chosen_slugs = router.addon.getSettingString('library.sync.chosen_lists').split(',')
        
        in_library = jsonrpc.library_shows_tvdbid()
        
        for i, chosen in enumerate(chosen_slugs):
            slug, user = chosen.split('.')
            list = metadata.trakt_list(user, slug, 'shows')
            for show in list:
                ids = show['show']['ids']
                tvdbid = ids['tvdb']
                if not refresh:
                    if tvdbid not in updates:
                        continue
                create_show(show, in_library, slug)
            create_trakt_playlist(user, slug, 'shows')
            progress.update(int((float(i) / len(chosen_slugs)) * 100))
    finally:
        progress.close()
    
    router.addon.setSettingString('trakt.last_sync_tv_lists',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)

    
@router.route('/library/sync/tv/watchlist')
def sync_show_watchlist(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding Watchlist TV Shows to Foxy Library')
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
                
        shows = metadata.trakt_watchlist(_type='shows', extended=True)
        in_library = jsonrpc.library_shows_tvdbid()
        for i, show in enumerate(shows):
            ids = show['show']['ids']
            tvdbid = ids['tvdb']
            if not refresh:
                if tvdbid not in updates:
                    continue
            create_show(show, in_library, 'watchlist')
            progress.update(int((float(i) / len(shows)) * 100))
    finally:
        progress.close()
    
    router.addon.setSettingString('trakt.last_sync_tv_watchlist',
                            time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.localtime(time.time())))
    
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)
