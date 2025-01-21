import sys
import shutil
import subprocess
from pathlib import Path

from tools.tools import str_paths

temp_dir = None

def remove_temp_files(exit=True):
    if temp_dir and temp_dir.exists():
        shutil.rmtree(temp_dir)
    if exit:
        sys.exit(1)

def execute(command, set_tool_path=True, get_stdout=True, exit_after_error=True):
    if set_tool_path:
        command[0] = str_paths[command[0]]

    try:
        out = subprocess.run(command, check=True, stdout=subprocess.PIPE)
        return out.stdout.decode() if get_stdout else True

    except Exception as e:
        decode = e.output.decode() if hasattr(e, 'output') else None

        if not exit_after_error:
            return decode, 1

        print(f"Error executing the following command:\n{command}\n{decode}\nExiting the script.")
        remove_temp_files()
