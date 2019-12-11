from functools import wraps
import json

import requests


API_KEY = 'AB2ED64C9BE51811'
API_URL = 'https://api.thetvdb.com/'
HEADERS = (('Content-Type', 'application/json'),)

def authenticate():
    data = {
        'apikey': API_KEY,
    }
    return requests.post(API_URL + 'login',
                         headers=dict(HEADERS),
                         data=json.dumps(data)).json()['token']


def get(token, path, **kwargs):
    headers = dict(HEADERS)
    headers['Authorization'] = 'Bearer {}'.format(token)
    return requests.get(API_URL + path,
                        headers=headers,
                        params=kwargs).json()


def jwt_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        jwt = getattr(jwt_auth, 'jwt', None)
        if not jwt:
            jwt = authenticate()
            setattr(jwt_auth, 'jwt', jwt)
        return func(jwt, *args, **kwargs)
    return wrapper
