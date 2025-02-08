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
from files.find_files import remove_duplicates_and_sort_fonts

def extract_orig_attachments():
    if os.path.exists(params.orig_attachs_dir):
        shutil.rmtree(params.orig_attachs_dir)

    for ind, fpath in enumerate(params.video_list
                                + params.subtitles_list, start=1):
        if params.mkv_split and ind > len(params.video_list):
            fpath, _, _ = params.matching_keys.get(fpath, (fpath, '', ''))

        if fpath.endswith(SUFFIXES['mkvtools_supported']):
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
    params.orig_fonts_list = []
    if not os.path.isdir(params.orig_attachs_dir):
        return

    dir_with_sep = path_methods.ensure_trailing_sep(params.orig_attachs_dir)
    for f in os.listdir(dir_with_sep):
        if f.endswith(SUFFIXES['fonts']):
            params.orig_fonts_list.append(f'{dir_with_sep}{f}')

def sort_orig_fonts():
    if not options.manager.get_merge_flag('sort_orig_fonts'):
        return

    if (params.rm_linking and
        len(params.fonts_list) != len(files.found.fonts)
        ):
        params.fonts_list = files.found.fonts.copy()

    extract_orig_attachments()
    set_extracted_orig_fonts()
    if params.orig_fonts_list:
        params.fonts_list = remove_duplicates_and_sort_fonts(
            params.fonts_list + params.orig_fonts_list)
