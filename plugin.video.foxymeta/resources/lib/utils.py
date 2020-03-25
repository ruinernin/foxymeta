import xbmc

import errno
import os
import re
import sys
import unicodedata

from xml.dom import minidom


def mkdir(path):
    if os.path.exists(path):
        return True
    
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EEXIST:
            pass
        else:
            raise
    else:
        return True


def get_valid_filename(filename):
    """Returns normalized ASCII filename."""
    ascii_name = filename
    try:
        ascii_name = unicodedata.normalize('NFKD', filename).encode('ascii',
                                                                    'ignore')
    except:
        log('{} could not be normalized'.format(filename))
    finally:
        ascii_name = ascii_name.replace(' ', '_')
        
    return re.sub(r'[^\w.-]', '', ascii_name)
    
    
def prettify_xml(xml):
    return minidom.parseString(xml).toprettyxml(indent='    ')
    
    
def log(msg, level=xbmc.LOGDEBUG):
    msg = '{}: {}'.format(sys.argv[0], msg)
    xbmc.log(msg, level)