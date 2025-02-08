import os
import re

import executor
import files.found
from files.constants import PATTERNS, SUFFIXES

def path_to_normpath(path):
    try:
        return os.path.normpath(path)

    except Exception as e:
        print(f'Error: path_to_normpath: {e}')
        executor.remove_temp_files()

def skip_sdir(sdir):
    if sdir in files.found.searched_dirs:
        return True

    sdir_wo_base = sdir[files.found.len_base_dir:]
    words = set(re.findall(r'\b\w+\b', sdir_wo_base))

    return True if words & PATTERNS['skip_dir'] else False

def ensure_trailing_sep(path):
    return f'{path}{files.found.sep}' if path[-1] != files.found.sep else path

def get_file_stem(fpath):
    return os.path.splitext(os.path.basename(fpath))[0]

def clean_tail(tail):
    while True:
        new_tail = re.sub(r'\.[a-zA-Z0-9]{1,3}\.', '', tail)
        if new_tail != tail:
            tail = new_tail
        else:
            break

    for ext in SUFFIXES['total_wo_fonts']:
        if tail.lower().startswith(ext):
            tail = tail[len(ext):]
        if tail.lower().endswith(ext):
            tail = tail[:-len(ext)]

    tail = tail.strip(' _.')
    if (tail.startswith('[') and
        tail.endswith(']') and
        tail.count('[') == 1
        ):
        tail = tail.strip('[]')

    return tail

def get_tail_file_stem(fpath, base_video):
    stem_fpath = get_file_stem(fpath)
    stem_base = get_file_stem(base_video)

    tail = stem_fpath[len(stem_base):]
    return clean_tail(tail) if len(tail) > 2 else tail

def get_name_file_dir(fpath):
    parent_dir = os.path.dirname(fpath)
    return os.path.basename(parent_dir)

def get_clean_name_file_dir(fpath):
    dir_name = get_name_file_dir(fpath)

    if (dir_name.startswith('[') and
        dir_name.endswith(']') and
        dir_name.count('[') == 1
        ):
        cleaned_dir_name = dir_name.strip(' _.[]')

    else:
        cleaned_dir_name = dir_name.strip(' _.')

    return cleaned_dir_name

def path_has_keyword(fpath, base_video, keywords):
    relative_dir = os.path.dirname(fpath).replace(
        os.path.dirname(base_video), '')
    tail = get_tail_file_stem(fpath, base_video)

    search_str = f'{relative_dir}/{tail}'.lower()
    words = set(re.findall(r'\b\w+\b', search_str))

    return True if words & keywords else False
