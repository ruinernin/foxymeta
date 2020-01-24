import errno
import os
import re
import unicodedata


def mkdir(path):
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
    ascii_name = unicodedata.normalize('NFKD', filename).encode('ascii',
                                                                'ignore')
    ascii_name = ascii_name.replace(' ', '_')
    return re.sub(r'[^\w.-]', '', ascii_name)