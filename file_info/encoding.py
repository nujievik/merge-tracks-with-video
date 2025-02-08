import os

import chardet

import path_methods
from files.constants import EXTENSIONS

def get_sub_charset_pcommand(fpath, tid):
    name, ext = os.path.splitext(fpath)

    if ext in EXTENSIONS['mkvtools_supported']:
        return []  # Mkvtool files already converted to UTF-

    if (ext == '.sub' and
        os.path.exists(f'{name}.idx')
        ):
        fpath = f'{name}.idx'  # .idx stores encode info

    with open (fpath, 'rb') as f:
        data = f.read()

    encoding = chardet.detect(data)['encoding']

    if (not encoding or
        encoding.lower().startswith(('utf-', 'ascii'))
        ):  # These encodes auto-detect by mkvmerge
        return []
    else:
        return ['--sub-charset', f'{tid}:{encoding}']
