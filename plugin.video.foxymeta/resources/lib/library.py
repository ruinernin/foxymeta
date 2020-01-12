import errno
import os

import xbmcgui

from . import metadata
from . import movies
from .router import router
from . import tv



def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EEXIST:
            pass
        else:
            raise
    else:
        return True


def imdb_nfo(imdbid):
    return 'http://www.imdb.com/title/{}/'.format(imdbid)


def tvdb_nfo(tvdbid):
    return 'http://thetvdb.com/?tab=series&id={}'.format(tvdbid)


def create_movie(imdbid):
    movie_dir = '{}/Library/Movies/{}'.format(router.addon_data_dir, imdbid)
    if not mkdir(movie_dir):
        return
    with open('{}/{}.nfo'.format(movie_dir, imdbid), 'w') as nfo:
        nfo.write(imdb_nfo(imdbid))
    with open('{}/{}.strm'.format(movie_dir, imdbid), 'w') as strm:
        strm.write(movies.foxy_movie_uri(imdbid))


def create_show(tvdbid):
    show_dir = '{}/Library/TV/{}'.format(router.addon_data_dir, tvdbid)
    if not mkdir(show_dir):
        return
    with open('{}/tvshow.nfo'.format(show_dir), 'w') as nfo:
        nfo.write(tvdb_nfo(tvdbid))


def create_episode(tvdbid, name, season, episode):
    season_dir = '{}/Library/TV/{}/Season {}'.format(router.addon_data_dir,
                                                     tvdbid,
                                                     season)
    mkdir(season_dir)
    ep_file = '{}/{} - S{:02d}E{:02d}.strm'.format(season_dir,
                                                   name,
                                                   int(season),
                                                   int(episode))
    with open(ep_file, 'w') as strm:
        strm.write(tv.foxy_tv_uri(tvdbid, season, episode))


@router.route('/library/sync/movies')
def sync_movie_collection():
    progress = xbmcgui.DialogProgress()
    progress.create('Adding Movies to Foxy Library')
    movies = metadata.trakt_collection(_type='movies')
    for movie in movies:
        imdbid = movie['movie']['ids']['imdb']
        create_movie(imdbid)
    progress.close()


@router.route('/library/sync/tv')
def sync_show_collection():
    progress = xbmcgui.DialogProgress()
    progress.create('Adding TV Shows to Foxy Library')
    shows = metadata.trakt_collection(_type='shows')
    for show in shows:
        tvdbid = show['show']['ids']['tvdb']
        name = show['show']['title']
        create_show(tvdbid)
        for season in metadata.tvdb_show(tvdbid)['airedSeasons']:
            if season == '0':
                continue
            for episode in metadata.tvdb_season(tvdbid, season):
                create_episode(tvdbid, name, season,
                               episode['airedEpisodeNumber'])
    progress.close()
