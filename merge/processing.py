import os

import executor
import files.found
import type_convert
import options.manager
import splitted.processing
from . import attachments, command_maker, errors, params
from . import set_orders, set_params

def execute_merge():
    set_orders.set_merge_info_orders()
    command = command_maker.get_merge_command()

    print(
        '\nGenerating a merged video file using mkvmerge. '
        'Executing the following command:'
        f'\n{type_convert.command_to_print_str(command)}'
    )

    lmsg = (
        'The command was executed successfully. The generated video '
        f'file was saved to:\n{params.out_file}'
    )

    command_out = executor.execute(command, exit_after_error=False)

    if options.manager.get_merge_flag('verbose'):
        if not isinstance(command_out, tuple):
            print(command_out)
        else:
            print(command_out[0])

    if not isinstance(command_out, tuple):
        print(lmsg)
    elif errors.error_handling(command_out[0], lmsg):
        execute_merge()

def split_or_something_else():
    splitted.processing.check_exist_split()

    if any(x for x in (
        params.mkv_split, params.audio_list, params.subtitles_list,
        params.fonts_list)
        ):
        return True
    else:
        return False

def merge_all_files():
    set_params.set_common_params()
    executor.temp_dir = params.temp_dir

    lim_gen = options.manager.get_option('lim_gen')
    start, end = options.manager.get_option('range_gen')
    start -= 1
    stems = sorted(files.found.stems_dict.keys())[start:end]

    for params.ind, params.stem in enumerate(stems, start):
        if params.count_gen >= lim_gen:
            break
        elif not set_params.set_current_params():
            continue

        params.fpath, params.fgroup = params.base_video, 'video'

        if params.base_video.endswith('.mkv'):
            if not split_or_something_else():
                continue

        set_params.set_out_file_path()
        if os.path.exists(params.out_file):
            params.count_gen_earlier += 1
            continue

        if params.mkv_split:
            splitted.processing.processing_segments()

        attachments.sort_orig_fonts()
        execute_merge()
        params.count_gen += 1

    executor.remove_temp_files(exit=False)
