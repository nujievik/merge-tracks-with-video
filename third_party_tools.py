import os
import sys

import executor

paths_to_tools = {
    'ffprobe': '',
    'mkvextract': '',
    'mkvinfo': '',
    'mkvmerge': ''
}

PACKAGE = {
    'ffmpeg': {
        'ffprobe'
    },
}
PACKAGE['mkvtoolnix'] = set(paths_to_tools.keys()) - PACKAGE['ffmpeg']

def available_tool(path):
    command = [path, '-h']
    stem, _ = os.path.splitext(os.path.basename(path))
    if stem in PACKAGE['ffmpeg']:
        command[1:1] = ['-v', 'quiet']

    return executor.execute(command, set_tool_path=False, get_stdout=False,
                            exit_after_error=False)

def find_tool(tool, tail):
    potential_paths = [
        f'{os.getcwd()}{os.sep}{tool}{tail}',
        tool,
    ]

    if getattr(sys, 'frozen', False):
        bundled = os.path.join(sys._MEIPASS, 'tools', f'{tool}{tail}')
        if os.path.exists(bundled):
            potential_paths.insert(0, bundled)

    if os.name == 'nt' and tool in PACKAGE['mkvtoolnix']:  # Windows
        potential_paths.extend([
            os.path.join(os.environ.get('PROGRAMFILES', ''),
                         'MkvToolNix', f'{tool}.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''),
                         'MkvToolNix', f'{tool}.exe'),
            os.path.join(os.path.expanduser('~'), 'Downloads',
                         'mkvtoolnix', f'{tool}.exe')
        ])

    for path in potential_paths:
        if available_tool(path):
            return path

def check_installation(package):
    if any(not paths_to_tools[tool] for tool in PACKAGE[package]):
        if package == 'mkvtoolnix':
            print(
                'Error: MKVToolNix is not installed. Please install '
                'MKVToolNix to default directory or to the current working '
                'directory and re-run the script:\n'
                'https://mkvtoolnix.download/downloads.html')

        elif package == 'ffmpeg':
            print(
                'Error: FFprobe (part of FFmpeg) is not installed. This tool '
                'is required for splitted MKV. Please install this tool to '
                'the current working directory (or to any directory and add '
                'it to the system Path) and re-run the script:\n'
                'https://ffmpeg.org/download.html')

        executor.remove_temp_files()

def set_tools_paths():
    tail = '.exe' if os.name == 'nt' else ''

    for tool in paths_to_tools:
        paths_to_tools[tool] = find_tool(tool, tail)

    check_installation('mkvtoolnix')
