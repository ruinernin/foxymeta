import json
import urllib

import xbmc
import xbmcgui
import xbmcplugin

from . import metadata
from .router import router
from . import ui



NATIVE = ('foxystreams',)
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


def foxy_tv_uri(_id, season, episode):
    base_uri = 'plugin://plugin.video.foxystreams/play/episode?'
    params = {
        'id': _id,
        'season': season,
        'episode': episode,
    }
    return base_uri + urllib.urlencode(params)


def movie_uri(ids, src='trakt'):
    if src == 'tmdb':
        ids = metadata.tmdbid_to_traktids(ids)
    player = router.addon.getSetting('player.movies.external').lower()
    if player == 'seren':
        return seren_movie_uri(ids['trakt'])
    elif player == 'foxystreams':
        return foxy_movie_uri(ids['imdb'])


@router.route('/play/movie')
def play_movie(get_metadata=True, **ids):
    player = router.addon.getSetting('player.movies.external').lower()
    if player not in NATIVE:
        xbmc.executebuiltin('RunPlugin("{}")'.format(movie_uri(ids)))
        return
    if get_metadata:
        movie_details = metadata.trakt_movie(ids['imdb'])
        li = ui.movie_listitem(trakt_data=movie_details)
    else:
        li = xbmcgui.ListItem()
    li.setPath(movie_uri(ids))
    xbmcplugin.setResolvedUrl(router.handle, True, li)
