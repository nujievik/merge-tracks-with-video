import os

import path_methods
from . import found, set_dirs
from .constants import PATTERNS, SUFFIXES

def skip_file(f):
    if (not '.' in f or
        any(pattern in f for pattern in PATTERNS['skip_file'])
        ):
        return True
    else:
        return False

def set_from_file_list(fnames, sdir):
    sdir = path_methods.ensure_trailing_sep(sdir)
    if path_methods.skip_sdir(sdir):
        return

    if fnames is None:
        fnames = os.listdir(sdir)

    for f in fnames:
        if skip_file(f):
            continue

        elif f.endswith(SUFFIXES['fonts']):
            found.fonts[f] = sdir

        elif f.endswith(SUFFIXES['total_wo_fonts']):
            for prefix in found.prefixes:
                if f.startswith(prefix):
                    stem, ext = f.rsplit('.', 1)
                    prf = prefix if prefix else stem

                    ext_files = found.stems_dict.setdefault(
                        prf, {}).setdefault('.' + ext, set())
                    ext_files.add(sdir + f)
                    break

    found.searched_dirs.add(sdir)

def recursive_search():
    for sdir, _, fnames in os.walk(found.start_dir):
        set_from_file_list(fnames, sdir)

def non_recursive_search():
    for sdir in found.search_dirs:
        set_from_file_list(None, sdir)

def replace_stems_in_stems_dict(stems_to_replace, sdir):
    for old, new in stems_to_replace.items():
        found.stems_dict[new] = found.stems_dict.pop(old)

    found.need_set_prefixes = True

def in_parent_dir(sdir):
    sdir = path_methods.ensure_trailing_sep(sdir)
    temp_fonts = {}
    stems_to_replace = {}
    added_exts = set()
    replace = False

    for f in os.listdir(sdir):
        if skip_file(f):
            continue

        elif f.endswith(SUFFIXES['fonts']):
            temp_fonts[f] = sdir

        elif f.endswith(SUFFIXES['total_wo_fonts']):
            stem, ext = f.rsplit('.', 1)
            add = False
            for prefix in found.prefixes:
                if not replace and f.startswith(prefix):
                    add = True
                    break

                if prefix.startswith(stem):
                    stems_to_replace[prefix] = stem
                    add = replace = True
                    break

            if add:
                ext = '.' + ext
                found.stems_dict[prefix].setdefault(
                    ext, set()).add(sdir + f)
                added_exts.add(ext)

    if stems_to_replace:
        replace_stems_in_stems_dict(stems_to_replace, sdir)

    if added_exts:
        set_dirs.by_added_exts(added_exts, sdir, temp_fonts)
        return True
    else:
        return False
