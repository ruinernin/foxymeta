import tmdb_api


def tmdb_poster(tmdb_id, resolution='w500'):
    movie = tmdb_api.get('/movie/{}'.format(tmdb_id))
    poster_path = movie['poster_path']
    return '{}/{}{}'.format(tmdb_api.IMAGE_URI,
                            resolution,
                            poster_path)
