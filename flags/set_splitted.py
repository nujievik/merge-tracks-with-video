from datetime import timedelta

import type_convert
import merge.params
from splitted import params
from . import merge, set_flag

def set_flags_by_splitted_params(tids):
    if params.splitted:
        options = ['--video-tracks', f'{params.tid}'] if len(tids) > 1 else []

        if all(not params.uids[ind] for ind in params.indexes):
            params.segments_vid = [params.video]

            str_times = ''
            for times in params.segments_times:
                start = type_convert.timedelta_to_str(times[0], hours_place=2, decimal_place=6)
                end = type_convert.timedelta_to_str(times[1], 2, 6)

                str_times += f',+{start}-{end}' if str_times else f'{start}-{end}'
                options.extend(['--split', f'parts:{str_times}'])

        else:
            params.extracted_orig = True

        if options:
            set_flag.for_flag(str(params.video), 'options', options)

    if params.extracted_orig or len(params.segments_vid) > 1 and merge.bool_flag('force_retiming'):
        params.extracted_orig = merge.params.extracted_orig = True
