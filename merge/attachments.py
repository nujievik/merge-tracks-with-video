import re
import shutil
from pathlib import Path

import executor
import flags.merge
import flags.set_flag
import files.find_ext
from . import params, set_params
from files.files import EXTENSIONS
from files.find import rm_duplicates_fonts_sort

def extract_orig_attachments():
    if params.orig_attachs_dir.exists():
        shutil.rmtree(params.orig_attachs_dir)

    for ind, fpath in enumerate(params.video_list + params.subs_list, start=1):
        if params.mkv_split and ind > len(params.video_list):
            fpath, _, _ = params.matching_keys.get(str(fpath), (fpath, None, None))

        if fpath.suffix in EXTENSIONS['mkvtools_supported']:
            names = []
            command = ['mkvmerge', '-i', str(fpath)]

            for line in executor.execute(command).splitlines():
                match = re.search(r"file name '(.+?)'", line)
                if match:
                    name = match.group(1)
                    names.append(name)

            command = ['mkvextract', str(fpath), 'attachments']
            for ind, name in enumerate(names, start=1):
                font = Path(params.orig_attachs_dir) / name
                command.append(f'{ind}:{str(font)}')

            if len(command) > 3:
                executor.execute(command, get_stdout=False)

                if ind > len(params.video_list):
                    flags.set_flag.for_flag(str(fpath), 'fonts', False)

def sort_orig_fonts():
    if not flags.merge.bool_flag('sort_orig_fonts'):
        return

    if params.rm_linking:
        set_params.set_file_lists(['fonts'])

    extract_orig_attachments()
    params.orig_fonts_list = files.find_ext.find_ext_files(params.orig_attachs_dir, EXTENSIONS['fonts'])

    if params.orig_fonts_list:
        params.fonts_list = rm_duplicates_fonts_sort(params.fonts_list + params.orig_fonts_list)
