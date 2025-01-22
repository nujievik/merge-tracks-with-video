import uuid
from pathlib import Path
from datetime import timedelta

import flags.merge
from . import params
from files.files import files

def set_common_params():
    param = flags.merge.get_flag.flag

    params.splitted_info = {}
    params.locale = param('locale')

    params.out_pname = param('out_pname')
    params.out_pname_tail = param('out_pname_tail')

    params.temp_dir = Path(param('save_dir')) / f'__temp_files__.{str(uuid.uuid4())[:8]}'
    params.orig_attachs_dir = Path(params.temp_dir) / 'orig_attachments'

    params.for_priority = param('for_priority')

    params.lim_gen = param('lim_gen')
    params.count_gen = 0
    params.count_gen_before = 0

def set_file_lists(fgroups=[]):
    param = flags.merge.bool_flag

    if not fgroups:
        fgroups = ['audio', 'subs']
        if params.orig_fonts_list or not params.fonts_list and files['fonts']:
            fgroups.append('fonts')

    for fgroup in fgroups:
        filepaths = []
        if param(fgroup):
            if fgroup != 'fonts':
                fpaths = files.get(fgroup, {}).get(str(params.video), [])
            else:
                fpaths = files.get('fonts', [])

            for fpath in fpaths:
                if param('files', fpath, fgroup):
                    filepaths.append(fpath)

        setattr(params, f'{fgroup}_list', filepaths)

    params.orig_fonts_list = []

def set_file_params():
    params.video_list = [params.video]
    param = flags.merge.bool_flag

    params.pro = param('pro')
    params.orig_fonts = param('orig_fonts')

    for fgroup in ['audio', 'subs', 'fonts']:
        value = not param(f'orig_{fgroup}') or files['directories'][fgroup] and flags.merge.flag(f'orig_{fgroup}') is None
        setattr(params, f'replace_{fgroup}', value)

    params.mkv_linking = params.mkv_cutted = params.mkv_split = False
    params.extracted_orig = params.rm_linking = False

    params.matching_keys = {}
    params.new_chapters = ''

    set_file_lists()

def set_output_path():
    if params.out_pname or params.out_pname_tail:
        num_digits = len(str(len(files['video'])))
        ind = f'{params.ind+1:0{num_digits}d}'

        stem = f'{params.out_pname}{ind}{params.out_pname_tail}'

    else:
        stem = params.video.stem

        if params.mkv_cutted:
            stem += '_cutted_video'
        elif params.mkv_linking:
            stem += '_merged_video'

        for fgroup in ['audio', 'subs', 'fonts']:
            if getattr(params, f'{fgroup}_list'):
                stem += f'_replaced_{fgroup}' if getattr(params, f'replace_{fgroup}') else f'_added_{fgroup}'

    params.output = Path(flags.merge.get_flag.flag('save_dir')) / f'{stem}.mkv'
