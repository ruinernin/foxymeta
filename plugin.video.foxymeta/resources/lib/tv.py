import datetime

from . import player
from . import metadata
from . import ui
from .player import foxy_tv_uri
from .router import router

import xbmcgui
import xbmcplugin

_trakt_access_token = router.addon.getSettingString('trakt.access_token')


TRAKT_AUTHED = bool(router.addon.getSettingString('trakt.access_token'))


@router.route('/tv')
def root():
    xbmcplugin.setContent(router.handle, 'files')
    router.gui_dirlist([(search, 'Search'),
                        (popular, 'Popular'),
                        (trending, 'Trending'),
                        (played, 'Most Played'),
                        (watched, 'Most Watched'),
                        (collected, 'Most Collected'),
                        (updates, 'Recently Updated')],
                       dirs=True, more=TRAKT_AUTHED)
    if TRAKT_AUTHED:
        router.gui_dirlist([(trakt_personal, 'My TV Shows')], dirs=True)


@router.route('/tv/trakt')
def trakt_personal():
    xbmcplugin.setContent(router.handle, 'files')
    router.gui_dirlist([(collection, 'Collection'),
                        (watchlist, 'Watchlist'),
                        (personal_lists, 'Personal Lists'),
                        (liked_lists, 'Liked Lists')],
                    dirs=True)


def ui_trakt_shows(func):
    def wrapper(page=1):
        _list = func()
        if _list is None:
            _list = func.__name__
        xbmcplugin.setContent(router.handle, 'tvshows')
        for show in metadata.trakt_shows(_list=_list,
                                         page=page):
            li = ui.show_listitem(trakt_data=show)
            xbmcplugin.addDirectoryItem(router.handle,
                                        router.build_url(
                                            tv_show,
                                            tvdbid=show['ids']['tvdb']),
                                        li,
                                        True)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(globals()[func.__name__],
                                                     page=int(page)+1),
                                    xbmcgui.ListItem('Next'),
                                    True)
        
        xbmcplugin.setContent(router.handle, 'tvshows')
        xbmcplugin.endOfDirectory(router.handle)
    return wrapper


@router.route('/tv/trakt/popular')
@ui_trakt_shows
def popular(page=1):
    pass


@router.route('/tv/trakt/trending')
@ui_trakt_shows
def trending(page=1):
    pass


@router.route('/tv/trakt/played')
@ui_trakt_shows
def played(page=1):
    pass


@router.route('/tv/trakt/watched')
@ui_trakt_shows
def watched(page=1):
    pass


@router.route('/tv/trakt/collected')
@ui_trakt_shows
def collected(page=1):
    pass


@router.route('/tv/trakt/updates')
@ui_trakt_shows
def updates(page=1):
    yesterday = datetime.datetime.utcnow() - datetime.timedelta(1)
    return 'updates/{}'.format(yesterday.strftime('%Y-%m-%d'))
    
    
@router.route('/tv/trakt/collection')
def collection():
    for item in metadata.trakt_collection(_type='shows', extended=True):
        show = item['show']
        li = ui.show_listitem(trakt_data=show)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(
                                        tv_show,
                                        tvdbid=show['ids']['tvdb']),
                                    li,
                                    True)
    xbmcplugin.setContent(router.handle, 'tvshows')
    xbmcplugin.endOfDirectory(router.handle)
    
    
@router.route('/tv/trakt/watchlist')
def watchlist():
    for item in metadata.trakt_watchlist(_type='shows', extended=True):
        show = item['show']
        li = ui.show_listitem(trakt_data=show)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(
                                        tv_show,
                                        tvdbid=show['ids']['tvdb']),
                                    li,
                                    True)
    xbmcplugin.setContent(router.handle, 'tvshows')
    xbmcplugin.endOfDirectory(router.handle)

    
@router.route('/tv/trakt/personal_lists')
def personal_lists():
    for _list in metadata.trakt_personal_lists():
        li = xbmcgui.ListItem(_list['name'])
        url = router.build_url(trakt_list,
                               user=_list['user']['ids']['slug'],
                               list_id=_list['ids']['trakt'])
        xbmcplugin.addDirectoryItem(router.handle,
                                    url,
                                    li, True)
    xbmcplugin.setContent(router.handle, 'files')
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/tv/trakt/liked_lists')
def liked_lists(page=1):
    for _list in metadata.trakt_liked_lists(page=page):
        li = xbmcgui.ListItem(_list['list']['name'])
        url = router.build_url(trakt_list,
                               user=_list['list']['user']['ids']['slug'],
                               list_id=_list['list']['ids']['trakt'])
        xbmcplugin.addDirectoryItem(router.handle,
                                    url,
                                    li, True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(liked_lists, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.setContent(router.handle, 'files')
    xbmcplugin.endOfDirectory(router.handle)
    
    
@router.route('/tv/trakt/list')
def trakt_list(user, list_id):
    for item in metadata.trakt_list(user, list_id, 'shows'):
        show = item['show']
        li = ui.show_listitem(trakt_data=show)
        li.setInfo('video', {
            'dateadded': ' '.join(item['listed_at'].split('.')[0].split('T')),
        })
        xbmcplugin.addDirectoryItem(router.handle,
                            router.build_url(
                                tv_show,
                                tvdbid=show['ids']['tvdb']),
                            li,
                            True)

    xbmcplugin.setContent(router.handle, 'tvshows')
    xbmcplugin.addSortMethod(router.handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.endOfDirectory(router.handle)
    

@router.route('/tv/trakt/search')
def search(query=None):
    if query is None:
        dialog = xbmcgui.Dialog()
        query = dialog.input('Search query:')
    for item in metadata.trakt_search(_type='show', query=query):
        show = item['show']
        li = ui.show_listitem(trakt_data=show)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(
                                        tv_show,
                                        tvdbid=show['ids']['tvdb']),
                                    li,
                                    True)
    xbmcplugin.setContent(router.handle, 'tvshows')
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/tv/tvdb/show')
def tv_show(tvdbid=None):
    xbmcplugin.setContent(router.handle, 'tvshows')
    for season in sorted(metadata.tvdb_show(tvdbid)['airedSeasons'], key=int):
        if season == '0':
            continue
        li = xbmcgui.ListItem('Season ' + season)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(
                                        tv_season,
                                        tvdbid=tvdbid,
                                        season=season),
                                    li,
                                    True)
    xbmcplugin.setContent(router.handle, 'tvshows')
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/tv/tvdb/season')
def tv_season(tvdbid=None, season=None):
    xbmcplugin.setContent(router.handle, 'episodes')
    for episode in metadata.tvdb_season(tvdbid, season):
        li = ui.episode_listitem(tvdb_data=episode)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(
                                        player.play_episode,
                                        _id=tvdbid,
                                        season=episode['airedSeason'],
                                        episode=episode['airedEpisodeNumber']),
                                    li,
                                    False)
    xbmcplugin.setContent(router.handle, 'episodes')
    xbmcplugin.endOfDirectory(router.handle)
