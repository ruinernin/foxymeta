import random

import xbmc

from resources.lib import library


def main():
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        library.sync_movie_collection()
        library.sync_show_collection()
        sleep_mins = 45 + int(random.random() * 15)
        if not monitor.waitForAbort(sleep_mins * 60):
            break


if __name__ == '__main__':
    main()
