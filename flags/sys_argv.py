import sys
from pathlib import Path

from . import args_processing, get_flag, set_flag

def set_flags_by_sys_argv():
    args = list(sys.argv[1:])
    args_processing.set_flags_by_args(args, args)

    if not get_flag.flag('save_dir', default_if_missing=False):
        set_flag.flag('save_dir', get_flag.flag('start_dir'))
