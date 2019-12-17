import time

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import metadata
from resources.lib.apis import trakt
from resources.lib.router import router

_periods = ['weekly', 'monthly', 'yearly', 'all']


@router.route('/trakt/popular')
def popular(page=1):
    for movie in metadata.trakt_movies(_list='popular', page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(popular, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.setPluginCategory(router.handle, 'Popular Movies')
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/trakt/played')
def played(page=1):
    set_period = router.addon.getSettingInt('list.time.period')
    for movie in metadata.trakt_movies(_list='played/{}'.format(_periods[set_period]), page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(played, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/trakt/trending')
def trending(page=1):
    for movie in metadata.trakt_movies(_list='trending', page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(trending, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)

    
@router.route('/trakt/watched')
def watched(page=1):
    set_period = router.addon.getSettingInt('list.time.period')
    for movie in metadata.trakt_movies(_list='watched/{}'.format(_periods[set_period]), page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(trending, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)
    

@router.route('/trakt/collected')
def collected(page=1):
    set_period = router.addon.getSettingInt('list.time.period')
    for movie in metadata.trakt_movies(_list='collected/{}'.format(_periods[set_period]), page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(trending, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)
    

@router.route('/trakt/anticipated')
def anticipated(page=1):
    for movie in metadata.trakt_movies(_list='anticipated', page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(trending, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)
    
    
@router.route('/trakt/boxoffice')
def boxoffice(page=1):
    for movie in metadata.trakt_movies(_list='boxoffice', page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(trending, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)
    
    
@router.route('/trakt/updates')
def updates(page=1):
    current_date = time.gmtime()
    start_date = time.strftime("%Y-%m-%d", current_date)

    for movie in metadata.trakt_movies(_list='updates/{}'.format(start_date), page=page):
        li = metadata.movie_listitem(trakt_data=movie)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(trending, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)
    
    
@router.route('/trakt/liked_lists')
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
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addSortMethod(router.handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.endOfDirectory(router.handle)



@router.route('/tmdb/trending')
def tmdb_trending(media_type='movie', page=1):
    result = metadata.tmdb_trending(media_type='movie', page=page)
    for item in result['results']:
        li = metadata.movie_listitem(tmdb_data=item)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(item['id'], src='tmdb'),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(tmdb_trending,
                                                 page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/')
def root():
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(popular),
                                xbmcgui.ListItem('Popular Movies'),
                                True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(trending),
                                xbmcgui.ListItem('Trending Movies'),
                                True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(tmdb_trending),
                                xbmcgui.ListItem('Trending Movies (TMDB)'),
                                True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(played),
                                xbmcgui.ListItem('Most Played Movies'),
                                True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(watched),
                                xbmcgui.ListItem('Most Watched Movies'),
                                True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(collected),
                                xbmcgui.ListItem('Most Collected Movies'),
                                True)                                
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(anticipated),
                                xbmcgui.ListItem('Most Anticipated Movies'),
                                True)                                         
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(boxoffice),
                                xbmcgui.ListItem('Box Office Top 10'),
                                True)                                         
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(updates),
                                xbmcgui.ListItem('Recently Updated Movies'),
                                True)                                         
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(liked_lists),
                                xbmcgui.ListItem('Liked Lists'),
                                True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(authenticate_trakt),
                                xbmcgui.ListItem('Auth Trakt'),
                                False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/auth_trakt')
def authenticate_trakt():
    init = trakt.authenticate()
    dialog = xbmcgui.DialogProgress()
    dialog.create('Enter code at: {}'.format(init['verification_url']),
                  init['user_code'])
    expires = time.time() + init['expires_in']
    while True:
        time.sleep(init['interval'])
        try:
            token = trakt.authenticate(init['device_code'])
        except Exception:
            pct_timeout = (time.time() - expires) / init['expires_in'] * 100
            pct_timeout = 100 - int(abs(pct_timeout))
            if pct_timeout >= 100 or dialog.iscanceled():
                dialog.close()
                xbmcgui.Dialog().notification('FoxyMeta', 'Trakt Auth failed')
                return
            dialog.update(int(pct_timeout))
        else:
            dialog.close()
            save_trakt_auth(token)
            return


def save_trakt_auth(response):
    router.addon.setSettingString('trakt.access_token',
                                  response['access_token'])
    router.addon.setSettingString('trakt.refresh_token',
                                  response['refresh_token'])
    expires = response['created_at'] + response['expires_in']
    router.addon.setSettingInt('trakt.expires', expires)


def openmeta_movie_uri(_id, src='imdb'):
    return 'plugin://plugin.video.openmeta/movies/play/{}/{}'.format(
        src,
        _id)


if __name__ == '__main__':
    xbmcplugin.setContent(router.handle, 'movies')
    router.run()
