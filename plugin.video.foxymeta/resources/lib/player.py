import datetime
import json
import urllib

import xbmc
import xbmcgui
import xbmcplugin

from . import jsonrpc
from . import metadata
from . import ui
from .router import router



NATIVE = ('foxystreams',)
FOXYSTREAMS_BASEURL = 'plugin://plugin.video.foxystreams/'
SEREN_BASEURL = 'plugin://plugin.video.seren/'
TMDBHELPER_BASEURL = 'plugin://plugin.video.themoviedb.helper/'


def seren_movie_uri(traktid):
    action_args = {
        'item_type': 'movie',
        'trakt_id': traktid,
    }
    params = {
        'action': 'getSources',
        'actionArgs': json.dumps(action_args),
    }
    
    return SEREN_BASEURL + '?' + urllib.urlencode(params)


def seren_tv_uri(traktid, season, episode):
    action_args = {
        'item_type': 'episode',
        'trakt_id': traktid,
        'season': season,
        'episode': episode,
    }
    params = {
        'action': 'getSources',
        'actionArgs': json.dumps(action_args),
    }
    
    return SEREN_BASEURL + '?' + urllib.urlencode(params)

def foxy_movie_uri(imdbid):
    return FOXYSTREAMS_BASEURL + 'play/movie?' + urllib.urlencode({'imdb': imdbid})


def foxy_tv_uri(_id, season, episode):
    params = {
        'id': _id,
        'season': season,
        'episode': episode,
    }
    return FOXYSTREAMS_BASEURL + 'play/episode?' + urllib.urlencode(params)


def tmdbhelper_movie_uri(tmdbid):
    params = {
        'info': 'play',
        'type': 'movie',
        'tmdb_id': tmdbid,
    }

    return TMDBHELPER_BASEURL + urllib.urlencode(params)


def tmdbhelper_tv_uri(_id, season, episode):
    params = {
        'info': 'play',
        'type': 'episode',
        'tmdb_id': tmdbid,
        'season': season,
        'episode': episode,
    }

    return TMDBHELPER_BASEURL + urllib.urlencode(params)


def movie_uri(ids, src='trakt'):
    if src == 'tmdb':
        ids = metadata.tmdbid_to_traktids(ids)
    player = router.addon.getSetting('player.movies.external').lower()
    if player == 'foxystreams':
        return foxy_movie_uri(ids['imdb'])
    elif player == 'seren':
        return seren_movie_uri(ids['trakt'])
    elif player == 'tmdbhelper':
        return tmdbhelper_movie_uri(ids['tmdb'])
    
        
    return None
    

def tv_uri(ids, season, episode, src='trakt'):
    if src == 'tmdb':
        ids = metadata.tmdbid_to_traktids(ids)
    player = router.addon.getSetting('player.tv.external').lower()
    if player == 'foxystreams':
        return foxy_tv_uri(ids['imdb'], season, episode)
    elif player == 'seren':
        return seren_tv_uri(ids['trakt'], season, episode)
    elif player == 'tmdbhelper':
        return tmdbhelper_tv_uri(ids['tmdb'], season, episode)

    return None
    

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
    xbmcgui.Window(10000).setProperty('foxymeta.nativeplay', 'True')


@router.route('/play/episode')
def play_episode(_id=None, season=None, episode=None):
    li = xbmcgui.ListItem()
    li.setPath(tv_uri(_id, season, episode))
    xbmcplugin.setResolvedUrl(router.handle, True, li)
    xbmcgui.Window(10000).setProperty('foxymeta.nativeplay', 'True')


class FoxyPlayer(xbmc.Player):
    """xbmc.Player object used for resume functionality."""

    @property
    def library_id(self):
        """Kodi libraryID of video being played.

        Returns the last return value from a previous call if playback
        is stopped.
        """
        info_tag = self.getVideoInfoTag()
        if self.is_episode:
            return jsonrpc.episode_library_id(info_tag.getTVShowTitle(),
                                              info_tag.getSeason(),
                                              info_tag.getEpisode())
        elif self.is_movie:
            return jsonrpc.movie_library_id(info_tag.getTitle())
        return None

    @property
    def is_episode(self):
        """True if currently playing item has 'episode' InfoTag.

        Returns the last return value from a previous call if playback
        is stopped.
        """
        return self.getVideoInfoTag().getMediaType() == 'episode'

    @property
    def is_movie(self):
        """True if currently playing item has 'movie' InfoTag.

        Returns the last return value from a previous call if playback
        is stopped.
        """
        return self.getVideoInfoTag().getMediaType() == 'movie'

    @property
    def resume_time(self):
        """Resume time for currently playing item in library.

        Returns the last return value from a previous call if playback
        is stopped.
        """
        if self.library_id:
            if self.is_movie:
                return jsonrpc.get_movie_resume(self.library_id)
            elif self.is_episode:
                return jsonrpc.get_episode_resume(self.library_id)
        return None

    def onPlayBackStarted(self):
        self.foxy_native = False
        if xbmcgui.Window(10000).getProperty('foxymeta.nativeplay') == 'True':
            self.foxy_native = True
            xbmcgui.Window(10000).clearProperty('foxymeta.nativeplay')

    def onAVStarted(self):
        """Ask user if they want to resume if a resume time is found."""
        if self.foxy_native:
            xbmc.sleep(2 * 1000)
            if self.is_episode:
                jsonrpc.set_episode_runtime(self.library_id,
                                            self.getTotalTime())
            seconds = self.resume_time
            if seconds:
                human_timestamp = str(datetime.timedelta(seconds=seconds))
                self.pause()
                if xbmcgui.Dialog().yesno("Resume at", human_timestamp):
                    self.seekTime(seconds)
                self.pause()
