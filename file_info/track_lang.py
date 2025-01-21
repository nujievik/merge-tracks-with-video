from pathlib import Path

import flags.merge
from . import mkvtools
from files.files import KEYS
from files.find_ext import path_has_keyword

def get_track_lang(tid, filepath, filegroup, base_video, tname):
    tlang = ''

    if filegroup != 'video':
        tlang = flags.merge.flag('tlang')

    if not tlang:
        tlang = mkvtools.get_file_info(filepath, 'Language:', tid)

    if not tlang:
        for lang, keys in KEYS['lang'].items():
            if path_has_keyword(base_video, filepath, keys):
                tlang = lang
            if path_has_keyword(Path(''), Path(tname), keys):
                tlang = lang

            if tlang:
                break

    return tlang
