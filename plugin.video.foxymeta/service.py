import random

import xbmc

from resources.lib.player import FoxyPlayer
from resources.lib import library
from resources.lib.router import router


def main():
    monitor = xbmc.Monitor()
    player = FoxyPlayer()
    while not monitor.abortRequested():
        if router.addon.getSettingString('trakt.access_token'):
            while player.isPlayingVideo():
                if monitor.waitForAbort(300):
                    return
            if router.addon.getSettingBool(
                   'library.sync.traktcollection.movies'):
                library.sync_movie_collection()
            if router.addon.getSettingBool('library.sync.traktcollection.tv'):
                library.sync_show_collection()
            if router.addon.getSettingString('library.sync.chosen_lists'):
                library.sync_movie_lists()
                library.sync_tv_lists()
        sleep_mins = 45 + int(random.random() * 15)
        if monitor.waitForAbort(sleep_mins * 60):
            return


if __name__ == '__main__':
    main()
