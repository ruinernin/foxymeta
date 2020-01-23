import xbmc


if __name__ == '__main__':
    dbtype = xbmc.getInfoLabel('ListItem.DBType')
    imdbid = xbmc.getInfoLabel('ListItem.IMDbNumber')
    
    path = 'RunPlugin(plugin://plugin.video.foxymeta/library/add/context?dbid={}&dbtype={})'
    xbmc.executebuiltin(path.format(imdbid, dbtype))
