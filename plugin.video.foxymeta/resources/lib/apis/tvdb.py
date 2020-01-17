import json
import time
from functools import wraps

import requests

from ..router import router


API_KEY = 'AB2ED64C9BE51811'
API_URL = 'https://api.thetvdb.com/'
IMAGE_URI = 'https://artworks.thetvdb.com/banners/'
HEADERS = (('Content-Type', 'application/json'),)

def authenticate():
    last_jwt = router.addon.getSetting('apis.tvdb.jwt')
    last_jwt_ts = router.addon.getSettingInt('apis.tvdb.jwt.epoch')
    if (time.time() - last_jwt_ts) < 3600:
        return last_jwt
    elif (time.time() - last_jwt_ts) < (3600 * 24):
        token = get(last_jwt, 'refresh_token')['token']
    else:
        data = {
            'apikey': API_KEY,
        }
        token = requests.post(API_URL + 'login',
                              headers=dict(HEADERS),
                              data=json.dumps(data)).json()['token']
    router.addon.setSetting('apis.tvdb.jwt', token)
    router.addon.setSettingInt('apis.tvdb.jwt.epoch', int(time.time()))
    return token


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
