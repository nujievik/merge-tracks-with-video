import os
import re
import shutil

import executor
import files.found
import path_methods
from . import params
import options.manager
import file_info.by_mkvtools
from files.constants import SUFFIXES

def extract_orig_attachments():
    if os.path.exists(params.orig_attachs_dir):
        shutil.rmtree(params.orig_attachs_dir)

    for ind, fpath in enumerate(params.video_list
                                + params.subtitles_list, start=1):
        if params.mkv_split and ind > len(params.video_list):
            fpath, _, _ = params.matching_keys.get(fpath, (fpath, '', ''))

        if not fpath.endswith(SUFFIXES['mkvtools_supported']):
            continue

        names = []
        stdout = file_info.by_mkvtools.get_mkvmerge_i_stdout(fpath)
        for line in stdout.splitlines():
            match = re.search(r"file name '(.+?)'", line)
            if match:
                name = match.group(1)
                names.append(name)

        command = ['mkvextract', fpath, 'attachments']
        for ind, name in enumerate(names, start=1):
            font = os.path.join(params.orig_attachs_dir, name)
            command.append(f'{ind}:{font}')

        if len(command) > 3:
            executor.execute(command, get_stdout=False)

            if ind > len(params.video_list):
                options.manager.set_target_option(fpath, 'fonts', False)

def set_extracted_orig_fonts():
    if not os.path.isdir(params.orig_attachs_dir):
        return

    dir_with_sep = path_methods.ensure_trailing_sep(params.orig_attachs_dir)
    for f in os.listdir(dir_with_sep):
        if f.endswith(SUFFIXES['fonts']):
            params.fonts_dict[f] = dir_with_sep

def set_fonts_list():
    params.fonts_dict = {}
    flg = options.manager.get_merge_flag

    if flg('sort_orig_fonts'):
        extract_orig_attachments()
        set_extracted_orig_fonts()
        if params.fonts_dict:
            params.extracted_orig_fonts = True

    if (params.fonts_dict or
        len(params.fonts_list) != len(files.found.fonts)
        ):
        params.fonts_list = []
        if flg('fonts'):
            params.fonts_dict.update(files.found.fonts)

        for name in sorted(params.fonts_dict.keys(), key=str.lower):
            params.fonts_list.append(f'{params.fonts_dict[name]}{name}')
