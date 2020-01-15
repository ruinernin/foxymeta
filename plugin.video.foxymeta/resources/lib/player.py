import json
import urllib

import xbmc
import xbmcgui
import xbmcplugin

from . import metadata
from .router import router



SEREN_BASEURL = 'plugin://plugin.video.seren/'


def seren_movie_uri(traktid):
    action_args = {
        'item_type': 'movie',
        'trakt_id': traktid,
    }
    params = {
        'action': 'getSources',
        'actionArgs': json.dumps(action_args),
    }
    uri = SEREN_BASEURL + '?' + urllib.urlencode(params)
    return uri


def foxy_movie_uri(imdbid):
    base_uri = 'plugin://plugin.video.foxystreams/play/movie?'
    return base_uri + urllib.urlencode({'imdb': imdbid})



def movie_uri(ids, src='trakt'):
    if src == 'tmdb':
        ids = metadata.tmdbid_to_traktids(ids)
    player = router.addon.getSetting('player.movies.external').lower()
    if player == 'seren':
        return seren_movie_uri(ids['trakt'])
    elif player == 'foxystreams':
        return foxy_movie_uri(ids['imdb'])


def library_movie_uri(ids):
    return 'plugin://plugin.video.foxymeta/play/movie?' + urllib.urlencode(ids)


@router.route('/play/movie')
def play_movie(**ids):
    player = router.addon.getSetting('player.movies.external').lower()
    if player == 'foxystreams':
        li = xbmcgui.ListItem(path=movie_uri(ids))
        xbmcplugin.setResolvedUrl(router.handle, True, li)
    else:
        xbmc.executebuiltin('RunPlugin("{}")'.format(movie_uri(ids)))
