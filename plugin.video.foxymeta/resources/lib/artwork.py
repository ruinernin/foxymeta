from .router import router
from . import tmdb_api


@router.cache
def tmdb_poster(tmdb_id, resolution='w500'):
    movie = tmdb_api.get('/movie/{}'.format(tmdb_id))
    poster_path = movie['poster_path']
    return '{}/{}{}'.format(tmdb_api.IMAGE_URI,
                            resolution,
                            poster_path)


@router.cache
def tmdb_backdrop(tmdb_id, resolution='w500'):
    movie = tmdb_api.get('/movie/{}'.format(tmdb_id))
    backdrop_path = movie['backdrop_path']
    return '{}/{}{}'.format(tmdb_api.IMAGE_URI,
                            resolution,
                            backdrop_path)
