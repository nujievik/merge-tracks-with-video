import os

from . import found
import path_methods
import options.manager
from .constants import EXTENSIONS, SUFFIXES

def set_dirs_by_start_doubles():
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
        found.searched_dirs.add(f'{found.start_dir}{found.sep}')

    if found.audio_dir or found.subtitles_dir:
        found.video_dir = found.start_dir
        if found.fonts:
            found.fonts_dir = found.start_dir
        return True
    else:
        return False

def replace_stems_in_stems_dict(stems_to_replace, sdir):
    for old, new in stems_to_replace.items():
        found.stems_dict[new] = found.stems_dict.pop(old)

    found.prefixes = tuple(found.stems_dict.keys())
    found.len_base_dir = len(sdir)  # Len directory with sep

def set_dirs_by_added_exts(added_exts, sdir, temp_fonts):
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

    found.searched_dirs.add(sdir)

def set_directory_files(sdir):
    sdir = path_methods.ensure_trailing_sep(sdir)
    temp_fonts = {}
    stems_to_replace = {}
    added_exts = set()
    replace = False

    for f in os.listdir(sdir):
        if f.endswith(SUFFIXES['fonts']):
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
                ext = f'.{ext}'
                found.stems_dict[prefix].setdefault(
                    ext, set()).add(f'{sdir}{f}')
                added_exts.add(ext)

    if stems_to_replace:
        replace_stems_in_stems_dict(stems_to_replace, sdir)

    if added_exts:
        set_dirs_by_added_exts(added_exts, sdir, temp_fonts)
        return True
    else:
        return False

def find_subsdir_after_audiodir():
    pass
    """
    temp_subtitles = set()
    for sdir, _, fnames in os.walk(found.video_dir):
        sdir = path_methods.ensure_trailing_sep(sdir)
        if path_methods.skip_sdir(sdir):
            continue

        for f in fnames:
            if f.endswith(SUFFIXES['subtitles']):
                temp_subtitles.add(f)
                break
    """

def find_fontdir():
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
                found.fonts_dir = os.path.normpath(sdir)
                return

def set_directories():
    if not set_dirs_by_start_doubles():
        limit = options.manager.get_option('lim_search_up')
        if not limit:
            return

        found.prefixes = tuple(found.stems_dict.keys())
        sdir = found.start_dir
        for _ in range(limit):
            sdir = os.path.dirname(sdir)
            if not sdir:
                return

            if set_directory_files(sdir):
                if found.audio_dir and not found.subtitles_dir:
                    find_subsdir_after_audiodir()
                break

    if found.subtitles_dir and not found.fonts_dir:
        find_fontdir()
