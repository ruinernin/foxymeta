import time

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import artwork
from resources.lib import metadata
from resources.lib.apis import trakt
from resources.lib.router import router


@router.route('/popular')
def popular(page=1):
    for movie in metadata.trakt_movies_popular(page=page):
        info = metadata.translate_info(metadata.TRAKT_TRANSLATION, movie)
        info['mediatype'] = 'movie'
        li = xbmcgui.ListItem(info['title'])
        li.setArt({
            'poster': artwork.tmdb_poster(movie['ids']['tmdb'],
                                          resolution='w780'),
            'fanart': artwork.tmdb_backdrop(movie['ids']['tmdb'],
                                            resolution='original')
        })
        li.setInfo('video', info)
        xbmcplugin.addDirectoryItem(router.handle,
                                    openmeta_movie_uri(movie['ids']['imdb']),
                                    li, False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(popular, page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.setContent(router.handle, 'movies')
    xbmcplugin.setPluginCategory(router.handle, 'Popular Movies')
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/')
def root():
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(popular),
                                xbmcgui.ListItem('Popular Movies'),
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


def openmeta_movie_uri(imdb_id):
    return 'plugin://plugin.video.openmeta/movies/play/imdb/{}'.format(
        imdb_id)


if __name__ == '__main__':
    router.run()
