import calendar
import datetime
import functools

from .router import router
from .apis import tmdb
from .apis import trakt
from .apis import tvdb



trakt.get = functools.partial(trakt.get,
                              auth_token=router.addon.getSettingString(
                                  'trakt.access_token'))
                                  
trakt.get_all = functools.partial(trakt.get_all,
                              auth_token=router.addon.getSettingString(
                                  'trakt.access_token'))


def trakt_movie(imdbid, extended='full'):
    path = 'movies/{}'.format(imdbid)
    result = trakt.get(path, extended=extended)
    return result


def trakt_search(_type='movie', query=None, page=1, all=False):
    path = 'search/{}'.format(_type)
    if all:
        result = list(trakt.get_all(path, query=query, extended='full'))
    else:
        result = trakt.get(path, query=query, extended='full', page=page)
    return result


def trakt_recommended(_type='movies'):
    path = 'recommendations/{}'.format(_type)
    result = trakt.get(path, extended='full', limit=50)
    return result


def trakt_movies(_list='popular', page=1, all=False):
    path = 'movies/{}'.format(_list)
    if all:
        result = list(trakt.get_all(path, extended='full'))
    else:
        result = trakt.get(path, extended='full', page=page)
    final = []
    # Some calls return items nested amongst data we don't care about such as
    # played/collected/watched counts, strip it and have homogenous API.
    for item in result:
        if 'movie' in item:
            final.append(item['movie'])
        else:
            final.append(item)
    return final


def trakt_shows(_list='popular', page=1, all=False):
    path = 'shows/{}'.format(_list)
    if all:
        result = list(trakt.get_all(path, extended='full'))
    else:
        result = trakt.get(path, extended='full', page=page)
    final = []
    # Some calls return items nested amongst data we don't care about such as
    # played/collected/watched counts, strip it and have homogenous API.
    for item in result:
        if 'show' in item:
            final.append(item['show'])
        else:
            final.append(item)
    return final


def trakt_show(imdbid):
    path = 'shows/{}'.format(imdbid)
    result = trakt.get(path, extended='full')
    return result


def trakt_seasons(imdbid, extended=False):
    path = 'shows/{}/seasons'.format(imdbid)
    if extended:
        result = trakt.get(path, extended='full,episodes')
    else:
        result = trakt.get(path)
    return result


def trakt_season(imdbid, season, extended=False):
    path = 'shows/{}/seasons/{:d}'.format(imdbid, int(season))
    if extended:
        result = trakt.get(path, extended='full')
    else:
        result = trakt.get(path)
    return result


def trakt_episode(imdbid, season, episode):
    path = 'shows/{}/seasons/{:d}/episodes/{:d}'.format(imdbid,
                                                        int(season),
                                                        int(episode))
    result = trakt.get(path, extended='full')
    return result


def trakt_personal_lists():
    user = trakt.get('users/me')['username']
    return trakt_users_lists(user)


def trakt_users_lists(user):
    path = 'users/{}/lists'.format(user)
    result = trakt.get(path)
    return result


def trakt_liked_lists(page=1, all=False):
    path = 'users/likes/lists'
    if all:
        result = list(trakt.get_all(path))
    else:
        result = trakt.get(path, page=page)
    return result


def trakt_collection(_type='movies', extended=False):
    path = 'sync/collection/{}'.format(_type)
    if extended:
        result = trakt.get(path, extended='full')
    else:
        result = trakt.get(path)
    return result
    
    
def trakt_watchlist(_type='movies', extended=False):
    path = 'sync/watchlist/{}'.format(_type)
    if extended:
        result = trakt.get(path, extended='full')
    else:
        result = trakt.get(path)
    return result


def trakt_list(user, list_id, _type, items=True):
    if items:
        path = 'users/{}/lists/{}/items/{}'.format(user, list_id, _type)
    else:
        path = 'users/{}/lists/{}'.format(user, list_id)
    result = trakt.get(path, extended='full')
    return result


@router.memcache
def tvdb_show(tvdb_seriesid):
    path = 'series/{}'.format(tvdb_seriesid)
    
    try:
        result = tvdb.get(path)['data']
    except KeyError:
        return []
        
    path = 'series/{}/episodes/summary'.format(tvdb_seriesid)
    result.update(tvdb.get(path)['data'])
    return result


def tvdb_show_images(tvdb_seriesid, keyType='fanart'):
    path = 'series/{}/images/query'.format(tvdb_seriesid)
    result = tvdb.get(path, keyType=keyType)
    return result


def tvdb_season(tvdb_seriesid, season):
    path = 'series/{}/episodes/query'.format(tvdb_seriesid)
    result = tvdb.get(path, airedSeason=season)['data']
    return result


def tvdb_episode(tvdb_episodeid):
    path = 'episodes/{}'.format(tvdb_episodeid)
    result = tvdb.get(path)
    return result


def tvdb_updates(epoch):
    path = 'updated/query'
    result = tvdb.get(path, fromTime=epoch)['data']
    return result


def tvdb_airdate_epoch(airdate):
    epoch = calendar.timegm(
        datetime.datetime.strptime(
            airdate,
            '%Y-%m-%d'
        ).utctimetuple()
    )
    return epoch


@router.memcache
def tmdb_movie(tmdb_id):
    return tmdb.get('/movie/{}'.format(tmdb_id))


@router.cache()
def tmdb_poster(tmdb_id, resolution='w780'):
    movie = tmdb_movie(tmdb_id)
    poster_path = movie['poster_path']
    return '{}/{}{}'.format(tmdb.IMAGE_URI,
                            resolution,
                            poster_path)


@router.cache()
def tmdb_backdrop(tmdb_id, resolution='w1280'):
    movie = tmdb_movie(tmdb_id)
    backdrop_path = movie['backdrop_path']
    return '{}/{}{}'.format(tmdb.IMAGE_URI,
                            resolution,
                            backdrop_path)


def tmdb_trending(page=1, media_type='movie', time_window='week'):
    path = '/trending/{}/{}'.format(media_type, time_window)
    return tmdb.get(path, page=page)


@router.cache()
def tvdb_poster(tvdbid):
    path = tvdb_show(tvdbid).get('poster', '')
    return tvdb.IMAGE_URI + path


@router.cache()
def tvdb_fanart(tvdbid):
    path = tvdb_show(tvdbid).get('fanart', '')
    return tvdb.IMAGE_URI + path


@router.cache()
def tmdbid_to_traktids(tmdbid):
    try:
        imdbid = tmdb.get('/movie/{}/external_ids'.format(tmdbid))['imdb_id']
    except tmdb.NotFound:
        raise
    else:
        return trakt_movie(imdbid, extended=None)['ids']
