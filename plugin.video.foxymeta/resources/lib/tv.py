import urllib

from . import metadata
from .router import router

import xbmcgui
import xbmcplugin



@router.route('/tv/trakt/popular')
def tv_popular(page=1):
    xbmcplugin.setContent(router.handle, 'tvshows')
    for show in metadata.trakt_shows(page=page):
        li = metadata.show_listitem(trakt_data=show)
        xbmcplugin.addDirectoryItem(router.handle,
                                    router.build_url(
                                        tv_show,
                                        tvdbid=show['ids']['tvdb']),
                                    li,
                                    True)
    xbmcplugin.addDirectoryItem(router.handle,
                                router.build_url(tv_popular,
                                                 page=int(page)+1),
                                xbmcgui.ListItem('Next'),
                                True)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/tv/tvdb/show')
def tv_show(tvdbid=None):
    xbmcplugin.setContent(router.handle, 'tvshows')
    for season in metadata.tvdb_show(tvdbid)['airedSeasons']:
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
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/tv/tvdb/season')
def tv_season(tvdbid=None, season=None):
    xbmcplugin.setContent(router.handle, 'episodes')
    for episode in metadata.tvdb_season(tvdbid, season):
        li = metadata.episode_listitem(tvdb_data=episode)
        xbmcplugin.addDirectoryItem(router.handle,
                                    foxy_tv_uri(tvdbid,
                                               episode['airedSeason'],
                                               episode['airedEpisodeNumber']),
                                    li,
                                    False)
    xbmcplugin.endOfDirectory(router.handle)


@router.route('/app/tv')
def root():
    router.gui_dirlist([(tv_popular, 'Popular TV')],
                       dirs=True)


def foxy_tv_uri(_id, season, episode):
    base_uri = 'plugin://plugin.video.foxystreams/play/episode?'
    params = {
        'id': _id,
        'season': season,
        'episode': episode,
    }
    return base_uri + urllib.urlencode(params)
