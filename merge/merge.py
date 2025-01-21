from pathlib import Path

import executor
import flags.merge
from files.files import files
from splitted import splitted
from . import attachments, execute, params, set_params

def merge_all_files():
    set_params.set_common_params()
    executor.temp_dir = params.temp_dir

    for params.ind, params.video in enumerate(files['video'][params.start_range:], start=params.start_range):
        params.filepath, params.filegroup = params.video, 'video'

        if params.count_gen >= params.lim_gen or params.ind > params.end_range:
            break
        if flags.merge.for_flag('files') is False:
            continue

        set_params.set_file_params()

        if params.video.suffix == '.mkv':
            splitted.check_exist_split()

            if all(not x for x in [params.mkv_split, params.audio_list, params.subs_list, params.fonts_list]):
                continue #skip video if not exist segment linking, external audio, subs or font

        set_params.set_output_path()
        if params.output.exists():
            params.count_gen_before += 1
            continue

        if params.mkv_split:
            splitted.processing_segments()

        attachments.sort_orig_fonts()
        execute.execute_merge()
        params.count_gen += 1

    executor.remove_temp_files(exit=False)
