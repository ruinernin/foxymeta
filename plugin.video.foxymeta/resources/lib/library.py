import errno
import os

import xbmcgui

from . import metadata
from . import movies
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


def create_movie(imdbid):
    movie_dir = '{}/Library/Movies/{}'.format(router.addon_data_dir, imdbid)
    if not mkdir(movie_dir):
        return
    with open('{}/{}.nfo'.format(movie_dir, imdbid), 'w') as nfo:
        nfo.write(imdb_nfo(imdbid))
    with open('{}/{}.strm'.format(movie_dir, imdbid), 'w') as strm:
        strm.write(movies.foxy_movie_uri(imdbid))


@router.route('/library/sync/movies')
def sync_movie_collection():
    progress = xbmcgui.DialogProgress()
    progress.create('Adding Movies to Foxy Library')
    movies = metadata.trakt_collection(_type='movies')
    for movie in movies:
        imdbid = movie['movie']['ids']['imdb']
        create_movie(imdbid)
    progress.close()
