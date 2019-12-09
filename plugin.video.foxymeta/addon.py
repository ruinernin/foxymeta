import itertools

import xbmcgui
import xbmcplugin

from .resources.lib import metadata
from .resources.lib.router import router


@router.route('/')
def root():
    for movie in itertools.islice(metadata.trat_movies_popular(), 20):
        info = metadata.translate_info(metadata.TRAKT_TRANSLATION, movie)
        li = xbmcgui.ListItem(info['title'])
        li.setInfo('video', info)
        xbmcplugin.addDirectoryItem(router.handle, '', li, False)
    xbmcplugin.endOfDirectory()


if __name__ == '__main__':
    router.run()
