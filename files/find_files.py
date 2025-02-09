import os

import path_methods
import options.manager
from .constants import PATTERNS, SUFFIXES
from . import constants, find_directories, found

def init_found_attributes():
    found.stems_dict = {}
    found.fonts = {}

    for attr in {'added_exts', 'search_dirs', 'searched_dirs'}:
        setattr(found, attr, set())
    for group in {'video', 'audio', 'subtitles', 'fonts'}:
        setattr(found, f'{group}_dir', '')

    found.prefixes = ['']
    found.sep = os.sep
    found.start_dir = options.manager.get_option('start_dir')
    found.search_dirs.add(found.start_dir)
    found.len_base_dir = len(found.start_dir) + 1  # +1 for sep

def set_files_from_list(fnames, sdir):
    sdir = path_methods.ensure_trailing_sep(sdir)
    if path_methods.skip_sdir(sdir):
        return

    if fnames is None:
        fnames = os.listdir(sdir)

    for f in fnames:
        if (not '.' in f or
            any(pattern in f for pattern in PATTERNS['skip_file'])
            ):
            continue

        if f.endswith(SUFFIXES['fonts']):
            found.fonts[f] = sdir

        elif f.endswith(SUFFIXES['total_wo_fonts']):
            for prefix in found.prefixes:
                if f.startswith(prefix):
                    stem, ext = f.rsplit('.', 1)
                    prf = prefix if prefix else stem

                    ext_files = found.stems_dict.setdefault(
                        prf, {}).setdefault(f'.{ext}', set())
                    ext_files.add(f'{sdir}{f}')

def set_files_recursive():
    for sdir, _, fnames in os.walk(found.start_dir):
        set_files_from_list(fnames, sdir)

def set_files_non_recursive():
    for sdir in found.search_dirs:
        set_files_from_list(None, sdir)

def remove_prefix_duplicates():
    prefixes = set(found.stems_dict.keys())
    removed = False
    for prefix in prefixes:
        if sum(prefix.startswith(prf) for prf in found.stems_dict) > 1:
            del found.stems_dict[prefix]
            removed = True

    if not removed:
        found.searched_dirs.add(f'{found.start_dir}{found.sep}')

def remove_stems_single_file():
    to_remove = set()
    single_mkv = set()
    exists_non_single = False

    for stem, exts in found.stems_dict.items():
        if (len(exts) == 1 and
            len(found.stems_dict[stem][next(iter(exts))]) == 1
            ):
            if '.mkv' in exts:
                single_mkv.add(stem)
            else:
                to_remove.add(stem)
        else:
            exists_non_single = True

    if exists_non_single:
        to_remove.update(single_mkv)

    for stem in to_remove:
        del found.stems_dict[stem]

def find_all_files():
    init_found_attributes()
    set_files_non_recursive()

    if not found.stems_dict:
        return

    if options.manager.is_option_or_condition('search_up',
                                              len(found.stems_dict) < 1000):
        find_directories.set_directories()
        if len(found.prefixes) != len(found.stems_dict):
            found.prefixes = tuple(found.stems_dict.keys())

        if found.video_dir:
            if len(found.search_dirs) > len(found.searched_dirs):
                set_files_non_recursive()
        else:
            set_files_recursive()

    else:
        remove_prefix_duplicates()
        found.prefixes = tuple(found.stems_dict.keys())
        set_files_recursive()

    remove_stems_single_file()
