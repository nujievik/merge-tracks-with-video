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

    if not params.setted_cp1251 and "textsubtitletrackcontainsinvalid8-bitcharacters" in cleaned_out:
        print("Invalid 8-bit characters in subs file!")
        for line in command_out.splitlines():
            if line.startswith("Warning") and "invalid 8-bit characters" in line:
                filename_match = re.search(r"'(/[^']+)'", line)
                filename = filename_match.group(1) if filename_match else None
                filepath = type_convert.str_to_path(filename)

                tid_match = re.search(r"track (\d+)", line)
                tid = tid_match.group(1) if tid_match else None

                if filepath and tid is not None:
                    flags.set_flag.for_flag(str(filepath), 'options', ['--sub-charset', f'{tid}:windows-1251'])
                    params.setted_cp1251 = True

        if params.setted_cp1251:
            print("Trying to generate with windows-1251 coding.")
            execute_merge()
            return

    if not cleaned_lline_out.startswith("error"):
        print(lmsg)

        if "thecodec'sprivatedatadoesnotmatch" in cleaned_out:
            print('Attention! The generated video file maybe corrupted because video parts have mismatched codec parameters.')
            if not params.rm_linking:
                print('Trying to generate another cutted version of the video without external video parts.')
                splitted.processing_codec_error()
                set_params.set_output_path()
                attachments.sort_orig_fonts()
                execute_merge()

    else:
        if "containschapterswhoseformatwasnotrecognized" in cleaned_lline_out:
            print(f"{last_line_out}\nTrying to generate without chapters.")
            flags.set_flag.for_flag(str(params.video), 'chapters', False)
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
        command_out = command_out[0]
        processing_error_warning_merge(command_out, lmsg)
