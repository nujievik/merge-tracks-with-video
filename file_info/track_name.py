import re
from pathlib import Path

import flags.merge
from . import mkvtools
from files.files import EXTENSIONS

def clean_tail(tail):
    while True:
        new_tail = re.sub(r'\.[a-zA-Z0-9]{1,3}\.', '', tail)
        if new_tail != tail:
            tail = new_tail
        else:
            break

    for ext in EXTENSIONS['video'].union(EXTENSIONS['audio'], EXTENSIONS['subs']):
        if tail.lower().startswith(ext):
            tail = tail[len(ext):]
        if tail.lower().endswith(ext):
            tail = tail[:-len(ext)]

    tail = tail.strip(' _.')
    if tail.startswith('[') and tail.endswith(']') and tail.count('[') == 1:
        tail = tail.strip('[]')

    return tail

def clean_dirname(dir_name):
    if dir_name.startswith('[') and dir_name.endswith(']') and dir_name.count('[') == 1:
        cleaned_dir_name = dir_name.strip(' _.[]')
    else:
        cleaned_dir_name = dir_name.strip(' _.')
    return cleaned_dir_name

def get_track_name_by_path(videopath, filepath):
    tail = filepath.stem[len(videopath.stem):]
    tail = clean_tail(tail) if len(tail) > 2 else tail

    return tail if len(tail) > 2 else clean_dirname(filepath.parent.name)

def get_track_name(tid, filepath, filegroup, base_video):
    if filegroup == 'video':
        tname = mkvtools.get_file_info(filepath, 'Name:', tid)

    else:
        tname = flags.merge.flag('tname', filepath, filegroup)
        if not tname:
            tname = mkvtools.get_file_info(filepath, 'Name:', tid)
        if not tname:
            tname = get_track_name_by_path(base_video, filepath)

    return tname
