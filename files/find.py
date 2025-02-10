import os

import options.manager
from . import found, set_dirs, set_files

def init_found_attributes():
    found.stems_dict = {}
    found.fonts = {}

    for attr in {'added_exts', 'search_dirs', 'searched_dirs'}:
        setattr(found, attr, set())
    for group in {'video', 'audio', 'subtitles', 'fonts'}:
        setattr(found, group + '_dir', '')

    found.prefixes = ['']
    found.need_set_prefixes = False
    found.sep = os.sep
    found.start_dir = options.manager.get_option('start_dir')
    found.search_dirs.add(found.start_dir)
    found.len_base_dir = len(found.start_dir) + 1  # +1 for sep

def set_prefixes_if_need():
    if (found.need_set_prefixes or
        len(found.prefixes) != len(found.stems_dict)
        ):
        found.prefixes = tuple(found.stems_dict.keys())
        found.need_set_prefixes = False

def find_in_parent_dirs():
    limit = options.manager.get_option('lim_search_up')
    if not limit:
        return

    found.prefixes = tuple(found.stems_dict.keys())
    sdir = found.start_dir
    for _ in range(limit):
        sdir = os.path.dirname(sdir)
        if not sdir:
            return

        if set_files.in_parent_dir(sdir):
            if found.audio_dir and not found.subtitles_dir:
                set_prefixes_if_need()
                set_dirs.subsdir_after_audiodir()
            break

def find_dirs():
    if not set_dirs.by_start_doubles():
        find_in_parent_dirs()

    if found.subtitles_dir and not found.fonts_dir:
        set_dirs.set_fontdir()

def remove_prefix_duplicates():
    prefixes = set(found.stems_dict.keys())
    removed = False
    for prefix in prefixes:
        if sum(prefix.startswith(prf) for prf in found.stems_dict) > 1:
            del found.stems_dict[prefix]
            removed = True

    if not removed:
        found.searched_dirs.add(found.start_dir + found.sep)

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

def all_files_and_dirs():
    init_found_attributes()
    set_files.non_recursive_search()
    found.searched_dirs = set()  # Clear for initial prefixes

    if not found.stems_dict:
        return

    if options.manager.is_option_or_condition('search_up',
                                              len(found.stems_dict) < 1000):
        find_dirs()
    else:
        remove_prefix_duplicates()

    if found.video_dir:
        if len(found.search_dirs) > len(found.searched_dirs):
            set_prefixes_if_need()
            set_files.non_recursive_search()
    else:
        set_prefixes_if_need()
        set_files.recursive_search()

    remove_stems_single_file()
