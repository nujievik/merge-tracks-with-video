import os
import sys
from pathlib import Path

import executor
from .tools import PACKAGE, str_paths

def available_tool(path):
    command = [str(path), '-h']
    if path.stem in PACKAGE['ffmpeg']:
        command[1:1] = ['-v', 'quiet']

    if executor.execute(command, set_tool_path=False, get_stdout=False, exit_after_error=False) is True:
        return True

def find_tool(tool, tail):
    potential_paths = [
        Path.cwd() / f'{tool}{tail}',
        Path(tool),
    ]

    if getattr(sys, 'frozen', False):
        bundled = Path(sys._MEIPASS) / f'tools/{tool}{tail}'
        if bundled.exists():
            potential_paths.insert(0, bundled)

    if os.name == 'nt' and tool in PACKAGE['mkvtoolnix']:  # Windows
        potential_paths.extend([
            Path(os.environ.get('PROGRAMFILES', '')) / 'MkvToolNix' / f'{tool}.exe',
            Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'MkvToolNix' / f'{tool}.exe',
            Path.home() / 'Downloads' / 'mkvtoolnix' / f'{tool}.exe'
        ])

    for path in potential_paths:
        if available_tool(path):
            return str(path)

def set_tools_paths():
    tail = '.exe' if os.name == 'nt' else ''

    for tool in str_paths:
        str_paths[tool] = find_tool(tool, tail)

    if any(not path for tool, path in str_paths.items() if tool in PACKAGE['mkvtoolnix']):
        print('Error! MKVToolNix is not installed. Please install MKVToolNix '
              'and re-run the script:\nhttps://mkvtoolnix.download/downloads.html')
        sys.exit(1)
