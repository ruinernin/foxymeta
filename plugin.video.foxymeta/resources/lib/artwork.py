from . import metadata
from . import tmdb_api
from .router import router


@router.cache
def tmdb_poster(tmdb_id, resolution='w780'):
    movie = metadata.tmdb_movie(tmdb_id)
    poster_path = movie['poster_path']
    return '{}/{}{}'.format(tmdb_api.IMAGE_URI,
                            resolution,
                            poster_path)


@router.cache
def tmdb_backdrop(tmdb_id, resolution='original'):
    movie = metadata.tmdb_movie(tmdb_id)
    backdrop_path = movie['backdrop_path']
    return '{}/{}{}'.format(tmdb_api.IMAGE_URI,
                            resolution,
                            backdrop_path)
