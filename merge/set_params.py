import os
import uuid
from datetime import timedelta

import files.found
from . import params
import options.manager
import file_info.setted
import file_info.by_mkvtools

def set_common_params():
    for attr in {'save_dir', 'locale', 'out_pname', 'out_pname_tail'}:
        setattr(params, attr, options.manager.get_option(attr))

    params.temp_dir = os.path.join(
        params.save_dir, f'__temp_files__.{str(uuid.uuid4())[:8]}')
    params.orig_attachs_dir = os.path.join(
        params.temp_dir, 'orig_attachments')

    params.out_num_digits = len(str(len(files.found.stems_dict)))
    params.count_gen = params.count_gen_earlier = 0

def clear_file_lists():
    for lst in {'video', 'audio', 'subtitles'}:
        setattr(params, f'{lst}_list', [])

def init_file_lists():
    for ext, fpaths in files.found.stems_dict[params.stem].items():
        for fpath in fpaths:
            fgroup = file_info.by_mkvtools.get_file_group(fpath)
            fgroup_list = getattr(params, f'{fgroup}_list')
            fgroup_list.append(fpath)

def filter_file_lists_by_flags():
    param = options.manager.get_merge_flag

    for fgroup in {'video', 'audio', 'subtitles'}:
        if param(fgroup):
            fpaths = [f for f in getattr(params, f'{fgroup}_list')
                      if param('files', f, fgroup)]
        else:
            fpaths = []
        setattr(params, f'{fgroup}_list', fpaths)

def set_fonts_list_if_need():
    if (not options.manager.get_merge_flag('fonts') or
        not files.found.fonts
        ):
        params.fonts_list = []

    # First pass; need for set_out_file and split_or_something_else
    elif (not params.fonts_list and
          files.found.fonts
        ):
        if len(files.found.fonts) != 1:
            params.fonts_list = ['']
        else:
            params.fonts_list = ['', '']

def set_file_lists():
    clear_file_lists()
    init_file_lists()
    filter_file_lists_by_flags()
    set_fonts_list_if_need()

def set_current_params():
    file_info.setted.info = {}
    set_file_lists()

    if params.video_list:
        params.base_video = params.video_list[0]
        file_info.setted.info['base_video'] = params.base_video
    else:
        return False

    param = options.manager.get_merge_flag
    params.pro = param('pro')
    params.orig_fonts = param('orig_fonts')

    for fgroup in {'audio', 'subtitles', 'fonts'}:
        value = not param(f'orig_{fgroup}') or (
            getattr(files.found, f'{fgroup}_dir') and
            options.manager.get_merge_option(f'orig_{fgroup}') is None
        )
        setattr(params, f'replace_{fgroup}', value)

    for attr in {
            'mkv_linking', 'mkv_cutted', 'mkv_split', 'extracted_orig',
            'rm_linking', 'rm_video_chapters', 'extracted_orig_fonts'
    }:
        setattr(params, attr, False)

    params.matching_keys = {}
    params.new_chapters = ''

    return True

def set_out_file_path():
    if params.out_pname or params.out_pname_tail:
        ind = f'{params.ind+1:0{params.out_num_digits}d}'
        stem = f'{params.out_pname}{ind}{params.out_pname_tail}'

    else:
        stem = params.stem

        if params.mkv_cutted:
            stem += '_cutted_video'
        elif params.mkv_linking:
            stem += '_merged_video'

        for fgroup in ('audio', 'subtitles', 'fonts'):
            if getattr(params, f'{fgroup}_list'):
                if getattr(params, f'replace_{fgroup}'):
                    stem += f'_replaced_{fgroup}'
                else:
                    stem += f'_added_{fgroup}'

    params.out_file = os.path.join(params.save_dir, f'{stem}.mkv')

def init_fid_part_cmd(fid):
    if not fid:  # For fid 0
        params.command_parts = {}
    cmd = params.command_parts.setdefault(fid, {})['cmd'] = []
    params.command_parts[fid]['position_to_insert'] = 0
    return cmd

def init_fde_flags_params():
    params.counters_fde_flags = {}
    params.langs_default_audio = set()
    params.default_locale_audio = False
    params.setted_false_enabled_subtitles = False
