import errno
import os
import shutil

import xbmc
import xbmcgui

from . import jsonrpc
from . import metadata
from . import movies
from . import tv
from .router import router



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


def clean_movies():
    """Remove all Movies."""
    movies_dir = '{}/Library/Movies/'.format(router.addon_data_dir)
    if not os.path.exists(movies_dir):
        return
    for movie in os.listdir(movies_dir):
        shutil.rmtree(movies_dir + movie)
    xbmc.executebuiltin('CleanLibrary(video)', wait=True)


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


def library_imdbids():
    """Return a list of imdbids existing in library."""
    result = jsonrpc.get_movies(properties=['imdbnumber'])
    return [movie['imdbnumber'] for movie in result.get('movies', list())]


@router.route('/library/sync/movies')
def sync_movie_collection(refresh=False):
    progress = xbmcgui.DialogProgressBG()
    progress.create('Adding Movies to Foxy Library')
    if refresh:
        clean_movies()
    movies = metadata.trakt_collection(_type='movies')
    in_library = library_imdbids()
    for movie in movies:
        imdbid = movie['movie']['ids']['imdb']
        if imdbid in in_library:
            continue
        create_movie(imdbid)
    progress.close()
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)


@router.route('/library/sync/tv')
def sync_show_collection():
    progress = xbmcgui.DialogProgressBG()
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
    xbmc.executebuiltin('UpdateLibrary(video)', wait=True)
