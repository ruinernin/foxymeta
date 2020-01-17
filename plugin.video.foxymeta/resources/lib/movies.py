import datetime
import functools
import urllib

import xbmcgui
import xbmcplugin

from . import metadata
from . import player
from .router import router
from .apis import tmdb
from . import ui

_trakt_access_token = router.addon.getSettingString('trakt.access_token')


TRAKT_AUTHED = bool(router.addon.getSettingString('trakt.access_token'))


@router.route('/movies')
def root():
    router.gui_dirlist([(search, 'Search'),
                        (popular, 'Popular'),
                        (trending, 'Trending'),
                        (tmdb_trending, 'Trending Movies (TMDb)'),
                        (played, 'Most Played'),
                        (watched, 'Most Watched'),
                        (collected, 'Most Collected')],
                       dirs=True, more=TRAKT_AUTHED)
    if TRAKT_AUTHED:
        router.gui_dirlist([(trakt_personal, 'My Movies')], dirs=True)


@router.route('/movies/trakt')
def trakt_personal():
    router.gui_dirlist([(recommended, 'Recommended'),
                        (collection, 'Collection'),
                        (personal_lists, 'Personal Lists'),
                        (liked_lists, 'Liked Lists')],
                       dirs=True)


def ui_trakt_list_movies(func, period=False):
    def wrapper(page=1):
        _list = func()
        if _list is None:
            _list = func.__name__
        if period:
            _list = '{}/{}'.format(_list,
                                   router.addon.getSettingString(
                                       'trakt.list_time_period').lower())
        for movie in metadata.trakt_movies(_list=_list, page=page):
            li = ui.movie_listitem(trakt_data=movie)
            xbmcplugin.addDirectoryItem(router.handle,
                                        router.build_url(player.play_movie,
                                                         **movie['ids']),
                                        li, False)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(globals()[func.__name__],
                                                     page=int(page)+1),
                                    xbmcgui.ListItem('Next'),
                                    True)
        xbmcplugin.endOfDirectory(router.handle)
    return wrapper


ui_trakt_list_movies_period = functools.partial(ui_trakt_list_movies,
                                                period=True)


@router.route('/movies/trakt/popular')
@ui_trakt_list_movies
def popular(page=1):
    pass


@router.route('/movies/trakt/played')
@ui_trakt_list_movies_period
def played(page=1):
    pass


@router.route('/movies/trakt/trending')
@ui_trakt_list_movies
def trending(page=1):
    pass


@router.route('/movies/trakt/watched')
@ui_trakt_list_movies_period
def watched(page=1):
    pass


@router.route('/movies/trakt/collected')
@ui_trakt_list_movies_period
def collected(page=1):
    pass


@router.route('/movies/trakt/anticipated')
@ui_trakt_list_movies
def anticipated(page=1):
    pass


@router.route('/movies/trakt/boxoffice')
@ui_trakt_list_movies
def boxoffice(page=1):
    pass


@router.route('/movies/trakt/search')
def search(query=None):
    if query is None:
        dialog = xbmcgui.Dialog()
        query = dialog.input('Search query:')
    for item in metadata.trakt_search(_type='movie', query=query):
        movie = item['movie']
        li = ui.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(player.play_movie,
                                                     **movie['ids']),
                                    li, False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/movies/trakt/updates')
@ui_trakt_list_movies
def updates(page=1):
    yesterday = datetime.datetime.utcnow() - datetime.timedelta(1)
    return 'updates/{}'.format(yesterday.strftime('%Y-%m-%d'))


@router.route('/movies/trakt/recommended')
def recommended():
    for movie in metadata.trakt_recommended(_type='movies'):
        li = ui.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(player.play_movie,
                                                     **movie['ids']),
                                    li, False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/movies/trakt/collection')
def collection():
    for item in metadata.trakt_collection(_type='movies', extended=True):
        movie = item['movie']
        li = ui.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(player.play_movie,
                                                     **movie['ids']),
                                    li, False)
    xbmcplugin.endOfDirectory(router.handle)
    
    
@router.route('/movies/trakt/watchlist')
def watchlist():
    for item in metadata.trakt_watchlist(_type='movies', extended=True):
        movie = item['movie']
        li = ui.movie_listitem(trakt_data=movie)
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(player.play_movie,
                                                     **movie['ids']),
                                    li, False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/movies/trakt/personal_lists')
def personal_lists():
    for _list in metadata.trakt_personal_lists():
        li = xbmcgui.ListItem(_list['name'])
        url = router.build_url(trakt_list,
                               user=_list['user']['ids']['slug'],
                               list_id=_list['ids']['trakt'])
        xbmcplugin.addDirectoryItem(router.handle,
                                    url,
                                    li, True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/movies/trakt/liked_lists')
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
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/movies/trakt/list')
def trakt_list(user, list_id):
    for item in metadata.trakt_list(user, list_id, 'movies'):
        movie = item['movie']
        li = ui.movie_listitem(trakt_data=movie)
        li.setInfo('video', {
            'dateadded': ' '.join(item['listed_at'].split('.')[0].split('T')),
        })
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(player.play_movie,
                                                     **movie['ids']),
                                    li, False)
    xbmcplugin.addSortMethod(router.handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/movies/tmdb/trending')
def tmdb_trending(media_type='movie', page=1):
    result = metadata.tmdb_trending(media_type='movie', page=page)
    for item in result['results']:
        li = ui.movie_listitem(tmdb_data=item)
        try:
            xbmcplugin.addDirectoryItem(router.handle,
                                        player.movie_uri(item['id'],
                                                         src='tmdb'),
                                        li, False)
        except tmdb.NotFound:
            pass
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(tmdb_trending,
                                                 page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)
