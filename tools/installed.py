import executor
from .tools import PACKAGE, str_paths

def ffmpeg():
    for tool in PACKAGE['ffmpeg']:
        if not str_paths[tool]:
            print('Error! FFprobe (part of FFmpeg) is not installed. This tool is required for splitted MKV. '
                  'Please install this tool, add to the OS Path and re-run the script:\nhttps://ffmpeg.org/download.html')
            executor.remove_temp_files()
