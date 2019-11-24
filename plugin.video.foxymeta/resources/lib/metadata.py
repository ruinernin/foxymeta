import functools

#from .router import router
from . import trakt_api
from . import tvdb_api


#trakt_api.get = functools.partial(trakt_api.get,
#                                  auth_token=router.addon.getString(
#                                      'trakt.auth_token'))
trakt_api.get = functools.partial(trakt_api.get,
                                  auth_token='')


TRAKT_TRANSLATION = (('title', 'title'),
                     ('year', 'year'),
                     ('overview', 'plot'),
                     ('released', 'premiered'),
                     ('certification', 'mpaa'),
                     ('genres', 'genres'),
                     (('ids', 'imdb'), 'imdbnumber'),
                     ('network', 'studio'),)


TVDB_EPISODE_TRANSLATION = (('episodeName', 'title'),
                            ('imdbId', 'imdbnumber'),
                            ('overview', 'plot'),
                            ('firstAired', 'aired'),)


def translate_info(translation, data):
    info_label = {}
    for data_key, info_label_key in translation:
        if isinstance(data_key, basestring):
            value = data.get(data_key)
        else:
            value = data
            for subkey in data_key:
                value = value.get(subkey, {})
        if value:
            info_label[info_label_key] = value
    return info_label


def trakt_movie(imdbid):
    path = 'movies/{}'.format(imdbid)
    result = trakt_api.get(path, extended='full')
    return result


def trakt_show(imdbid):
    path = 'shows/{}'.format(imdbid)
    result = trakt_api.get(path, extended='full')
    return result


def trakt_seasons(imdbid, extended=False):
    path = 'shows/{}/seasons'.format(imdbid)
    if extended:
        result = trakt_api.get(path, extended='full,episodes')
    else:
        result = trakt_api.get(path)
    return result


def trakt_season(imdbid, season, extended=False):
    path = 'shows/{}/seasons/{:d}'.format(imdbid, int(season))
    if extended:
        result = trakt_api.get(path, extended='full')
    else:
        result = trakt_api.get(path)
    return result


def trakt_episode(imdbid, season, episode):
    path = 'shows/{}/seasons/{:d}/episodes/{:d}'.format(imdbid,
                                                        int(season),
                                                        int(episode))
    result = trakt_api.get(path, extended='full')
    return result


@tvdb_api.jwt_auth
def tvdb_show(jwt, tvdb_seriesid):
    path = 'series/{}/episodes/summary'.format(tvdb_seriesid)
    result = tvdb_api.get(jwt, path)
    return result


@tvdb_api.jwt_auth
def tvdb_season(jwt, tvdb_seriesid, season):
    path = 'series/{}/episodes/query'.format(tvdb_seriesid)
    result = tvdb_api.get(jwt, path, airedSeason=season)
    return result


@tvdb_api.jwt_auth
def tvdb_episode(jwt, tvdb_episodeid):
    path = 'episodes/{}'.format(tvdb_episodeid)
    result = tvdb_api.get(jwt, path)
    return result
