import re
from pathlib import Path

import executor
import type_convert
import flags.merge
import flags.set_flag
from splitted import splitted
from . import attachments, merge_command, params, set_params

def processing_error_warning_merge(command_out, lmsg):
    cleaned_out = ''.join(command_out.split()).lower()
    last_line_out = command_out.splitlines()[-1]
    cleaned_lline_out = ''.join(last_line_out.split()).lower()

    if 'warning:' in cleaned_out:
        for line in command_out.splitlines():
            if line.lower().startswith('warning:'):
                print(line)

    if not cleaned_lline_out.startswith("error"):
        print(lmsg)

        if "thecodec'sprivatedatadoesnotmatch" in cleaned_out:
            print('Attention! The generated video file maybe corrupted because video parts have mismatched codec parameters.')
            if not params.rm_linking:
                print('Trying to generate another cutted version of the video without external video parts.')
                splitted.processing_codec_error()
                attachments.sort_orig_fonts()
                params.output = Path(str(params.output).replace('_merged_', '_cutted_'))
                execute_merge()

    else:
        if "containschapterswhoseformatwasnotrecognized" in cleaned_lline_out:
            print(f"{last_line_out}\nTrying to generate without chapters.")
            flags.set_flag.for_flag(str(params.video), 'chapters', False)
            execute_merge()

        elif all(x in cleaned_lline_out for x in ["thetypeoffile", "couldnotberecognized"]):
            filepath = Path(last_line_out.split("'")[1])

            if any(str(x) == str(filepath) for x in params.video_list):
                print(f"{last_line_out}\nUnrecognized video file! Exiting the script")
                executor.remove_temp_files()

            print(f"{last_line_out}\nTrying to generate without this file.")
            filepath = Path(last_line_out.split("'")[1])

            params.audio_list = [x for x in params.audio_list if str(x) != str(filepath)]
            params.subs_list = [x for x in params.subs_list if str(x) != str(filepath)]
            execute_merge()

        elif "nospaceleft" in cleaned_lline_out:
            if params.output.exists():
                params.output.unlink()
            print(f"Error writing file!\nPlease re-run the script with other save directory.")
            executor.remove_temp_files()

        else:
            if params.output.exists():
                params.output.unlink()
            print(f"Error executing the command!\n{last_line_out}\nExiting the script.")
            executor.remove_temp_files()

def execute_merge():
    command = merge_command.get_merge_command()

    print('\nGenerating a merged video file using mkvmerge. Executing the following command: '
          f'\n{type_convert.command_to_print_str(command)}')

    lmsg = f"The command was executed successfully. The generated video file was saved to:\n{str(params.output)}"

    command_out = executor.execute(command, exit_after_error=False)
    if flags.merge.bool_flag('extended_log'):
        print(command_out) if not isinstance(command_out, tuple) else print(command_out[0])

    if not isinstance(command_out, tuple):
        print(lmsg)
    else:
        processing_error_warning_merge(command_out[0], lmsg)
