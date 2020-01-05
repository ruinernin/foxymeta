import datetime
import functools
import urllib

import xbmcgui
import xbmcplugin

from . import metadata
from .router import router
from .apis import tmdb, trakt


@router.route('/movies')
def root():
    trakt_token = router.addon.getSettingString('trakt.access_token')
    router.gui_dirlist([(search, 'Search'),
                        (popular, 'Popular Movies'),
                        (trending, 'Trending Movies'),
                        (tmdb_trending, 'Trending Movies (TMDB)'),
                        (played, 'Most Played Movies'),
                        (watched, 'Most Watched Movies'),
                        (collected, 'Most Collected Movies'),
                        (anticipated, 'Most Anticipated Movies'),
                        (boxoffice, 'Box Office Top 10'),
                        (updates, 'Recently Updated Movies')],
                       dirs=True,  more=trakt_token)
    if trakt_token:
        router.gui_dirlist([(collection, 'Collection'),
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
                                       'list.time.period').lower())
        for movie in metadata.trakt_movies(_list=_list, page=page):
            li = metadata.movie_listitem(trakt_data=movie)
            li.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(router.handle,
                                        foxy_movie_uri(movie['ids']['imdb']),
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
        li = metadata.movie_listitem(trakt_data=movie)
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(router.handle,
                                    foxy_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/movies/trakt/updates')
@ui_trakt_list_movies
def updates(page=1):
    yesterday = datetime.datetime.utcnow() - datetime.timedelta(1)
    return 'updates/{}'.format(yesterday.strftime('%Y-%m-%d'))


@router.route('/movies/trakt/collection')
def collection(_type='movies'):
    for item in metadata.trakt_collection(_type=_type):
        movie = item['movie']
        li = metadata.movie_listitem(trakt_data=movie)
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(router.handle,
                                    foxy_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/trakt/personal_lists')
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


@router.route('/trakt/list')
def trakt_list(user, list_id):
    for item in metadata.trakt_list(user, list_id, 'movies'):
        movie = item['movie']
        li = metadata.movie_listitem(trakt_data=movie)
        li.setInfo('video', {
            'dateadded': ' '.join(item['listed_at'].split('.')[0].split('T')),
        })
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(router.handle,
                                    foxy_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addSortMethod(router.handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/movies/tmdb/trending')
def tmdb_trending(media_type='movie', page=1):
    result = metadata.tmdb_trending(media_type='movie', page=page)
    for item in result['results']:
        li = metadata.movie_listitem(tmdb_data=item)
        li.setProperty('IsPlayable', 'true')
        try:
            xbmcplugin.addDirectoryItem(router.handle,
                                        foxy_movie_uri(item['id'], src='tmdb'),
                                        li, False)
        except tmdb.NotFound:
            pass
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(tmdb_trending,
                                                 page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.cache()
def foxy_movie_uri(_id, src='imdb'):
    base_uri = 'plugin://plugin.video.foxystreams/play/movie?'
    if src == 'tmdb':
        res = tmdb.get('/movie/{}/external_ids'.format(_id))
        try:
            _id = tmdb.get('/movie/{}/external_ids'.format(_id))['imdb_id']
        except tmdb.NotFound:
            raise
    return base_uri + urllib.urlencode({'imdb': _id})
