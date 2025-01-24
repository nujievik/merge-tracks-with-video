from pathlib import Path

import flags.merge
from . import mkvtools
from .keys import KEYS
from files.find_ext import path_has_keyword

def get_track_lang(tid, filepath, filegroup, base_video, tname):
    tlang = ''

    if filegroup != 'video':
        tlang = flags.merge.flag('tlang')

    if not tlang:
        tlang = mkvtools.get_file_info(filepath, 'Language', tid)

    if not tlang or tlang not in KEYS['lang']:
        for lang, keys in KEYS['lang'].items():
            if (tlang in keys or
                path_has_keyword(base_video, filepath, keys) or
                path_has_keyword(Path(''), Path(tname), keys)):
                tlang = lang

            if tlang and tlang in KEYS['lang']:
                break

    return tlang
