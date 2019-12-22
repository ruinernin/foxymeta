import functools
import time
import urllib

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import metadata, movies
from resources.lib.apis import tmdb, trakt
from resources.lib.router import router



@router.route('/tv/trakt/popular')
def tv_popular(page=1):
    for show in metadata.trakt_shows(page=page):
        li = xbmcgui.ListItem(show['title'])
        xbmcplugin.addDirectoryItem(router.handle,
                                    '',
                                    li,
                                    False)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(tv_popular,
                                                 page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/app/tv')
def tv():
    router.gui_dirlist([(tv_popular, 'Popular TV')],
                       dirs=True)


@router.route('/')
def root():
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(movies.root),
                                xbmcgui.ListItem('Movies'),
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
    dialog.create('FoxyMeta: Authorize Trakt',
                  ('Enter the following code at:\n'
                   '{url}\n\n'
                   '{code}').format(url=init['verification_url'],
                                    code=init['user_code']))
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
                xbmcgui.Dialog().notification('FoxyMeta',
                                              'Trakt Authorization Failed')
                return
            dialog.update(int(pct_timeout))
        else:
            dialog.close()
            save_trakt_auth(token)
            xbmcgui.Dialog().notification('FoxyMeta',
                                          'Trakt Authorization Succeeded')
            return


@router.route('/revoke_trakt')
def revoke_trakt():
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('FoxyMeta: Revoke Trakt',
                          ('Are you sure you want to revoke authorization with'
                           ' Trakt.tv?'))
    if not choice:
        return
    result = trakt.revoke(router.addon.getSettingString('trakt.access_token'))
    if result.status_code == 200:
        router.addon.setSettingString('trakt.access_token', '')
        router.addon.setSettingString('trakt.refresh_token', '')
        router.addon.setSettingString('trakt.username', '')
        router.addon.setSettingInt('trakt.expires', 0)
        xbmcgui.Dialog().notification('FoxyMeta', 'Trakt Authorization Revoked')


def save_trakt_auth(response):
    username = trakt.get('users/me', response['access_token'])['username']
    router.addon.setSettingString('trakt.access_token',
                                  response['access_token'])
    router.addon.setSettingString('trakt.refresh_token',
                                  response['refresh_token'])
    expires = response['created_at'] + response['expires_in']
    router.addon.setSettingInt('trakt.expires', expires)
    router.addon.setSettingString('trakt.username', username)


if __name__ == '__main__':
    xbmcplugin.setContent(router.handle, 'movies')
    router.run()
