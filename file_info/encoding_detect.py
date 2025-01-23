from pathlib import Path

import chardet

from files.files import EXTENSIONS

def get_sub_charset_pcommand(filepath, tid):
    if filepath.suffix in EXTENSIONS['mkvtools_supported']:
        return []

    if filepath.suffix == '.sub' and filepath.with_suffix('.idx').exists():
        filepath = filepath.with_suffix('.idx') #.idx stores encode info

    with filepath.open('rb') as f:
        data = f.read()

    encoding = chardet.detect(data)['encoding']

    if not encoding:
        return []
    elif encoding.lower().startswith(('utf-', 'ascii')):
        return [] #mkvmerge auto-detect this encode
    else:
        return ['--sub-charset', f'{tid}:{encoding}']
