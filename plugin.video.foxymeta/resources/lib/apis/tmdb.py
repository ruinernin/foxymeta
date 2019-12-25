import requests


BASE_URI = 'https://api.themoviedb.org/3'
API_KEY = '1248868d7003f60f2386595db98455ef'
IMAGE_URI = 'https://image.tmdb.org/t/p'


class NotFound(Exception):
    pass


def get(path, **kwargs):
    params = kwargs
    params['api_key'] = API_KEY
    result = requests.get(BASE_URI + path, params=params)
    if result.status_code == 404:
        raise NotFound(path)
    return result.json()
