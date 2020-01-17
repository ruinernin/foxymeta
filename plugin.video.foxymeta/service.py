import random

import xbmc

from resources.lib import library
from resources.lib.router import router


def main():
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if not router.addon.getSettingString('trakt.access_token'):
            return
        if router.addon.getSettingBool('library.sync.traktcollection.movies'):
            library.sync_movie_collection()
        if router.addon.getSettingBool('library.sync.traktcollection.tv'):
            library.sync_show_collection()
        sleep_mins = 45 + int(random.random() * 15)
        if not monitor.waitForAbort(sleep_mins * 60):
            break


if __name__ == '__main__':
    main()
