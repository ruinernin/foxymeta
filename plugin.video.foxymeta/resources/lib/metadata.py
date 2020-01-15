import functools

from .router import router
from .apis import tmdb
from .apis import trakt
from .apis import tvdb

import xbmcgui


trakt.get = functools.partial(trakt.get,
                              auth_token=router.addon.getSettingString(
                                  'trakt.access_token'))


TRAKT_TRANSLATION = (('title', 'title'),
                     ('year', 'year'),
                     ('overview', 'plot'),
                     ('released', 'premiered'),
                     ('certification', 'mpaa'),
                     ('genres', 'genre'),
                     (('ids', 'imdb'), 'imdbnumber'),
                     ('network', 'studio'),)


TVDB_TRANSLATION = (('episodeName', 'title'),
                    ('airedSeason', 'season'),
                    ('airedEpisodeNumber', 'episode'),
                    ('imdbId', 'imdbnumber'),
                    ('overview', 'plot'),
                    ('firstAired', 'aired'),)


TMDB_TRANSLATION = (('title', 'title'),
                    ('release_date', 'premiered'),
                    ('overview', 'plot'),)


def translate_info(translation, data):
    info_label = {}
    for data_key, info_label_key in translation:
        try:
            basestring
        except NameError:
            basestring = str
        if isinstance(data_key, basestring):
            value = data.get(data_key)
        else:
            value = data
            for subkey in data_key:
                value = value.get(subkey, {})
        if value:
            if info_label_key == 'genre':
                value = [genre.capitalize() for genre in value]
            info_label[info_label_key] = value
    return info_label


def show_listitem(trakt_data=None):
    info = {
        'mediatype': 'tvshow',
    }
    art = {}
    if trakt_data:
        info.update(translate_info(TRAKT_TRANSLATION, trakt_data))
        art['poster'] = tvdb_poster(trakt_data['ids']['tvdb'])
        art['fanart'] = tvdb_fanart(trakt_data['ids']['tvdb'])
    li = xbmcgui.ListItem(info['title'])
    li.setInfo('video', info)
    li.setArt(art)
    return li


def episode_listitem(trakt_data=None, tvdb_data=None):
    info = {
        'mediatype': 'episode',
    }
    art = {}
    if trakt_data:
        info.update(translate_info(TRAKT_TRANSLATION, trakt_data))
    if tvdb_data:
        info.update(translate_info(TVDB_TRANSLATION, tvdb_data))
        art['thumb'] = tvdb.IMAGE_URI + tvdb_data['filename']
    li = xbmcgui.ListItem(info['title'])
    li.setInfo('video', info)
    li.setArt(art)
    return li


def movie_listitem(trakt_data=None, tmdb_data=None):
    info = {
        'mediatype': 'movie',
    }
    tmdbid = None
    if trakt_data:
        info.update(translate_info(TRAKT_TRANSLATION, trakt_data))
        tmdbid = trakt_data['ids']['tmdb']
        imdbid = trakt_data['ids']['imdb']
    if tmdb_data:
        info.update(translate_info(TMDB_TRANSLATION, tmdb_data))
        tmdbid = tmdb_data['id']
    li = xbmcgui.ListItem(info['title'])
    li.setInfo('video', info)
    if tmdb_data:
        li.setArt({
            'poster': '{}/{}{}'.format(tmdb.IMAGE_URI, 'w780',
                                      tmdb_data['poster_path']),
            'fanart': '{}/{}{}'.format(tmdb.IMAGE_URI, 'w1280',
                                      tmdb_data['backdrop_path']),
        })
    elif tmdbid:
        art = {}
        try:
            art['poster'] = tmdb_poster(tmdbid, resolution='w780')
        except (KeyError, tmdb.NotFound):
            pass
        try:
            art['fanart'] = tmdb_backdrop(tmdbid, resolution='w1280')
        except (KeyError, tmdb.NotFound):
            pass
        li.setArt(art)
    if imdbid:
        import library
        li.addContextMenuItems([('Add to FoxyMeta Library',
                                 ('RunPlugin(plugin://plugin.video.foxymeta/'
                                  'library/add/movie?imdbid={})')
                                  .format(imdbid))])
    return li


def trakt_movie(imdbid, extended='full'):
    path = 'movies/{}'.format(imdbid)
    result = trakt.get(path, extended=extended)
    return result


def trakt_search(_type='movie', query=None, page=1):
    path = 'search/{}'.format(_type)
    result = trakt.get(path, query=query, extended='full', page=1)
    return result


def trakt_recommended(_type='movies'):
    path = 'recommendations/{}'.format(_type)
    result = trakt.get(path, extended='full', limit=50)
    return result


def trakt_movies(_list='popular', page=1):
    path = 'movies/{}'.format(_list)
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


def trakt_shows(_list='popular', page=1):
    path = 'shows/{}'.format(_list)
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
    path = '/users/{}/lists'.format(user)
    result = trakt.get(path)
    return result


def trakt_liked_lists(page=1):
    path = '/users/likes/lists'
    result = trakt.get(path, page=page)
    return result


def trakt_collection(_type='movies', extended=False):
    path = '/sync/collection/{}'.format(_type)
    if extended:
        result = trakt.get(path, extended='full')
    else:
        result = trakt.get(path)
    return result


def trakt_list(user, list_id, _type):
    path = '/users/{}/lists/{}/items/{}'.format(user, list_id, _type)
    result = trakt.get(path, extended='full')
    return result


@router.memcache
@tvdb.jwt_auth
def tvdb_show(jwt, tvdb_seriesid):
    path = 'series/{}'.format(tvdb_seriesid)
    result = tvdb.get(jwt, path)['data']
    path = 'series/{}/episodes/summary'.format(tvdb_seriesid)
    result.update(tvdb.get(jwt, path)['data'])
    return result


@tvdb.jwt_auth
def tvdb_show_images(jwt, tvdb_seriesid, keyType='fanart'):
    path = 'series/{}/images/query'.format(tvdb_seriesid)
    result = tvdb.get(jwt, path, keyType=keyType)
    return result


@tvdb.jwt_auth
def tvdb_season(jwt, tvdb_seriesid, season):
    path = 'series/{}/episodes/query'.format(tvdb_seriesid)
    result = tvdb.get(jwt, path, airedSeason=season)['data']
    return result


@tvdb.jwt_auth
def tvdb_episode(jwt, tvdb_episodeid):
    path = 'episodes/{}'.format(tvdb_episodeid)
    result = tvdb.get(jwt, path)
    return result


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
    path = tvdb_show(tvdbid)['poster']
    return tvdb.IMAGE_URI + path


@router.cache()
def tvdb_fanart(tvdbid):
    path = tvdb_show(tvdbid)['fanart']
    return tvdb.IMAGE_URI + path


@router.cache()
def tmdbid_to_traktids(tmdbid):
    try:
        imdbid = tmdb.get('/movie/{}/external_ids'.format(tmdbid))['imdb_id']
    except tmdb.NotFound:
        raise
    else:
        return trakt_movie(imdbid, extended=None)['ids']
