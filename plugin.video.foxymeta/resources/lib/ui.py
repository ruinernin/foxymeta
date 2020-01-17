import xbmcgui

from . import metadata
from .apis import tmdb
from .apis import tvdb



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
        art['poster'] = metadata.tvdb_poster(trakt_data['ids']['tvdb'])
        art['fanart'] = metadata.tvdb_fanart(trakt_data['ids']['tvdb'])
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
    li.setProperty('IsPlayable', 'true')
    return li


def movie_listitem(trakt_data=None, tmdb_data=None):
    info = {
        'mediatype': 'movie',
    }
    tmdbid = None
    if trakt_data:
        info.update(translate_info(TRAKT_TRANSLATION, trakt_data))
        tmdbid = trakt_data['ids']['tmdb']
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
            art['poster'] = metadata.tmdb_poster(tmdbid, resolution='w780')
        except (KeyError, tmdb.NotFound):
            pass
        try:
            art['fanart'] = metadata.tmdb_backdrop(tmdbid, resolution='w1280')
        except (KeyError, tmdb.NotFound):
            pass
        li.setArt(art)
    li.setProperty('IsPlayable', 'true')
    return li
