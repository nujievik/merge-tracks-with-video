import os

import path_methods
import merge.set_orders
from . import found, set_files
from .constants import EXTENSIONS, SUFFIXES

def by_start_doubles():
    double_prefixes = {
        prefix for prefix, exts in found.stems_dict.items()
        if (len(exts) > 1 or
            sum(prefix.startswith(prf) for prf in found.stems_dict) > 1)
    }
    removed_stem = False

    for double in double_prefixes:
        exts = found.stems_dict[double].keys()

        if exts & EXTENSIONS['subtitles']:
            found.subtitles_dir = found.start_dir
        elif exts & EXTENSIONS['audio']:
            found.audio_dir = found.start_dir

        if len(exts) == 1:  # Contains in another short prefix
            del found.stems_dict[double]
            removed_stem = True

    if not removed_stem:
        found.searched_dirs.add(found.start_dir + found.sep)

    if found.audio_dir or found.subtitles_dir:
        found.video_dir = found.start_dir
        if found.fonts:
            found.fonts_dir = found.start_dir
        return True
    else:
        return False

def by_added_exts(added_exts, sdir, temp_fonts):
    groups = ['video', 'subtitles', 'audio']
    groups = [g for g in groups if not getattr(found, f'{g}_dir')]
    setted = 0

    for group in groups:
        if added_exts & EXTENSIONS[group]:
            setattr(found, f'{group}_dir', sdir[:-1])
            groups = [g for g in groups if g != group]
            setted += 1
            if setted >= len(added_exts):
                break

    if groups:
        for _, exts in found.stems_dict.items():
            exts = set(exts)
            earlier_added_exts = exts - added_exts
            for group in groups:
                if earlier_added_exts & EXTENSIONS[group]:
                    setattr(found, f'{group}_dir', found.start_dir)
                    setted += 1
                    if setted >= len(earlier_added_exts):
                        break

            if any(getattr(found, f'{group}_dir') for group in groups):
                break

    if temp_fonts and not found.fonts_dir:
        font = next(iter(temp_fonts))
        found.fonts_dir = temp_fonts[font][:-1]
        found.fonts.update(temp_fonts)

    found.len_base_dir = len(sdir)  # Len directory with sep
    found.search_dirs.add(sdir)
    found.searched_dirs.add(sdir)

def subsdir_after_audiodir():
    temp_subtitles = []
    for sdir, _, fnames in os.walk(found.video_dir):
        sdir = path_methods.ensure_trailing_sep(sdir)
        if path_methods.skip_sdir(sdir):
            continue

        for f in fnames:
            if set_files.skip_file(f):
                continue

            elif (f.endswith(SUFFIXES['subtitles']) and
                  f.startswith(found.prefixes)
                  ):
                temp_subtitles.append(sdir + f)
                break

    if temp_subtitles:
        temp_file_groups = merge.set_orders.set_files_info(
            temp_subtitles, ['subtitles'])
        merge.set_orders.set_files_order(temp_file_groups)

        file_paths = merge.set_orders.file_info.setted.info['file_paths']
        if file_paths:
            found.subtitles_dir = os.path.dirname(file_paths[0])
            found.search_dirs.add(found.subtitles_dir)

def set_fontdir():
    potentials = [found.subtitles_dir]
    if found.subtitles_dir != found.video_dir:
        potentials.append(os.path.dirname(found.subtitles_dir))
    searched = set()

    for directory in potentials:
        for sdir, _, fnames in os.walk(directory):
            sdir = path_methods.ensure_trailing_sep(sdir)
            if sdir in searched:
                continue
            searched.add(sdir)

            for f in fnames:
                if f.endswith(SUFFIXES['fonts']):
                    found.fonts[f] = sdir
            if found.fonts:
                found.fonts_dir = sdir[:-1]
                return
