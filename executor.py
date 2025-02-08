import os
import sys
import shutil
import subprocess

import type_convert
import third_party_tools

temp_dir = None

def remove_temp_files(exit=True):
    if temp_dir is not None and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    if exit:
        print('Exiting the script.')
        sys.exit(1)

def execute(command, set_tool_path=True, get_stdout=True,
            exit_after_error=True):

    if set_tool_path:
        command[0] = third_party_tools.paths_to_tools[command[0]]

    try:
        out = subprocess.run(command, check=True, stdout=subprocess.PIPE)
        return out.stdout.decode() if get_stdout else True

    except Exception as e:
        decode = e.output.decode() if hasattr(e, 'output') else ''

        if not exit_after_error:
            return (decode, 1) if get_stdout else False

        print(f'Error executing the following command:\n'
              f'{type_convert.command_to_print_str(command)}\n{decode}')
        remove_temp_files()
