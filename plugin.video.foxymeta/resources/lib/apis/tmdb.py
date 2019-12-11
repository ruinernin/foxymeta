import requests


BASE_URI = 'https://api.themoviedb.org/3'
API_KEY = '1248868d7003f60f2386595db98455ef'
IMAGE_URI = 'https://image.tmdb.org/t/p'

def get(path, **kwargs):
    params = kwargs
    params['api_key'] = API_KEY
    return requests.get(BASE_URI + path, params=params).json()
