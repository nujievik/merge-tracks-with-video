import os

import path_methods
import options.manager
from . import by_mkvtools, setted
from files.constants import PATTERNS

def get_track_lang(tid, fpath, fgroup, base_video, tname):
    tid_info = setted.info.setdefault(fpath, {}).setdefault(tid, {})

    if tid_info.get('tlang', None) is not None:
        return tid_info['tlang']

    tlang = ''

    if fgroup != 'video':
        tlang = options.manager.get_merge_option('tlang')

    if not tlang:
        tlang = by_mkvtools.get_info_by_query('Language', fpath, tid)

    if not tlang or tlang not in PATTERNS['languages']:
        for lang, keys in PATTERNS['languages'].items():
            if (tlang in keys or
                path_methods.path_has_keyword(fpath, base_video, keys) or
                path_methods.path_has_keyword(tname, '', keys)
                ):
                tlang = lang

            if tlang in PATTERNS['languages']:
                break

    tid_info['tlang'] = tlang
    return tlang
