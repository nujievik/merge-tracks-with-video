import json
import os
import subprocess
import sys

from constants import TOOLS

tool_paths = {x: x for x in TOOLS['names']}

def _set_tool_paths():
    def _available_tool(path):
        command = [path, '-h']
        return execute(command, exit_on_error=False, get_stdout=False,
                       set_tool_path=False)

    def _find_path(tool):
        potential_paths = [
            f'{cwd}{sep}{tool}{ext}',
            tool,
        ]
        if getattr(sys, 'frozen', False):
            bundled = (
                f'{sys._MEIPASS}{sep}tools{sep}{tool}{ext}')
            if os.path.exists(bundled):
                potential_paths.insert(0, bundled)

        if os.name == 'nt' and tool in TOOLS['packages']['mkvtoolnix']:
            potential_paths.extend([
                os.path.join(os.environ.get('PROGRAMFILES', ''),
                             'MkvToolNix', f'{tool}.exe'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', ''),
                             'MkvToolNix', f'{tool}.exe'),
                os.path.join(os.path.expanduser('~'), 'Downloads',
                             'mkvtoolnix', f'{tool}.exe')
            ])

        for path in potential_paths:
            if _available_tool(path):
                return path

    global tool_paths
    cwd = os.getcwd()
    ext = '.exe' if os.name == 'nt' else ''
    sep = os.sep

    for tool in tool_paths:
        tool_paths[tool] = _find_path(tool)

def check_package(package):
    if any(not tool_paths[tool] for tool in TOOLS['packages'][package]):
        if package == 'mkvtoolnix':
            print(
                'Error: MKVToolNix is not installed. Please install '
                'MKVToolNix to default directory or to the current '
                'working directory and re-run the script:\n'
                'https://mkvtoolnix.download/downloads.html'
            )
        elif package == 'ffmpeg':
            print(
                'Error: FFprobe (part of FFmpeg) is not installed. This '
                'tool is required for splitted MKV. Please install it to '
                'the current working directory (or to any directory and '
                'add the directory to the system Path) and re-run the '
                'script:\nhttps://ffmpeg.org/download.html'
            )
        sys.exit(1)

def _command_to_print_str(command):
    name_tool = os.path.basename(command[0])
    return (f"'{name_tool}' "
            + f"{' '.join(f"'{item}'" for item in command[1:])}")

def execute(command, **kwargs):
    # Some correction of the command
    if kwargs.get('quiet', True) and command[0].endswith(TOOLS['quiet']):
        _add = ['-v', 'quiet']
        if command[1:3] != _add:
            command[1:1] = _add
    if kwargs.get('set_tool_path', True):
        command[0] = tool_paths.get(command[0], command[0])

    # Print message if need
    verbose = kwargs.get('verbose', None)
    if verbose:
        if kwargs.get('msg', ''):
            print(kwargs['msg'])
        print('Executing the following command:')
        print(_command_to_print_str(command))

    get_stdout = kwargs.get('get_stdout', True)
    to_json = kwargs.get('to_json', None)
    try:
        if to_json:
            with open(to_json, 'w') as file:
                json.dump(command[1:], file, indent=4)
            _command = [command[0], f'@{to_json}']
        else:
            _command = command

        out = subprocess.run(_command, check=True, stdout=subprocess.PIPE)
        return out.stdout.decode() if get_stdout else True

    except Exception as e:
        exit_on_error = kwargs.get('exit_on_error', True)
        if not exit_on_error and not get_stdout:
            return False

        decode = e.output.decode() if hasattr(e, 'output') else ''

        if not exit_on_error:
            return (decode, 1)

        else:
            if verbose:  # The command was printed above
                print(f'Error executing the command.\n{decode}')
            else:
                print(f'Error executing the following command:\n'
                        f'{_command_to_print_str(command)}\n{decode}')
            sys.exit(1)

def init():
    _set_tool_paths()
    check_package('mkvtoolnix')  # Main tools, always required

if __name__ == '__main__':
    init()
