import json
import time
from functools import wraps

import requests

from ..router import router


API_KEY = 'AB2ED64C9BE51811'
API_URL = 'https://api.thetvdb.com/'
IMAGE_URI = 'https://artworks.thetvdb.com/banners/'
HEADERS = (('Content-Type', 'application/json'),)
TOKEN = None

def authenticate():
    global TOKEN
    TOKEN = router.addon.getSetting('apis.tvdb.jwt')
    last_jwt_ts = router.addon.getSettingInt('apis.tvdb.jwt.epoch')
    if (time.time() - last_jwt_ts) < 3600:
        return
    elif (time.time() - last_jwt_ts) < (3600 * 24):
        TOKEN = get('refresh_token')['token']
    else:
        data = {
            'apikey': API_KEY,
        }
        TOKEN = requests.post(API_URL + 'login',
                              headers=dict(HEADERS),
                              data=json.dumps(data)).json()['token']
    router.addon.setSetting('apis.tvdb.jwt', TOKEN)
    router.addon.setSettingInt('apis.tvdb.jwt.epoch', int(time.time()))


def jwt_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if TOKEN is None:
            authenticate()
        return func(*args, **kwargs)
    return wrapper


@jwt_auth
def get(path, **kwargs):
    headers = dict(HEADERS)
    headers['Authorization'] = 'Bearer {}'.format(TOKEN)
    return requests.get(API_URL + path,
                        headers=headers,
                        params=kwargs).json()
