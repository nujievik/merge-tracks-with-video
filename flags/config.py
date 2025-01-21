import sys
import configparser
from pathlib import Path

from . import args_processing

def set_flags_by_config():
    config = configparser.ConfigParser()
    ini = Path.cwd() / 'config-generate-video-with-these-files.ini'

    try:
        config.read(ini)
    except Exception:
        print(f"Error: Incorrect config in the file '{ini}'.\nPlease fix or remove the config and re-run the script.")
        sys.exit(1)

    sections = config.sections()

    args, displays = [], []
    for section in sections:
        for key, value in config.items(section):
            args.append(f'-{key}={value}')
            displays.append(f'{key} = {value}')

    args_processing.set_flags_by_args(args, displays, ini)
