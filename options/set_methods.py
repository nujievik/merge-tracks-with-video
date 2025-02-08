import os
import sys
import locale
import configparser

import merge.params
import splitted.params
from . import arg_handler, manager
from files.constants import PATTERNS
from .values import SEPARATE_TARGET_OPTIONS, setted

def set_locale():
    for element in locale.getlocale():
        locale_words = set(element.split('_'))
        for lang, keys in PATTERNS['languages'].items():
            if keys & locale_words:
                manager.set_option('locale', lang)
                return

def set_options_by_args(args, displays, config=None):
    target_key = None
    target_options = []
    add_msg = f" in the config file '{config}'" if config else ''

    for ind, arg in enumerate(args):
        r = arg_handler.get_key_and_value(arg, target_key, target_options)
        key, value, target_key, target_options = r

        if key == 'target':
            pass
        elif target_key:
            if key in SEPARATE_TARGET_OPTIONS and value is not None:
                manager.set_target_option(target_key, key, value)
            else:
                target_options.append(arg.strip('\'"'))

        elif key and value is not None:
            manager.set_option(key, value)
        else:
            print(
                f"Error: unrecognized argument '{displays[ind]}'{add_msg}."
                "\nPlease fix it and re-run the script.")
            sys.exit(1)

    if target_key and target_options:
        manager.set_target_option(target_key, 'specials', target_options)

def set_options_by_config():
    config = configparser.ConfigParser()
    ini = f'{os.getcwd()}{os.sep}config-merge-tracks-with-video.ini'

    try:
        config.read(ini)
    except Exception:
        print(
            f"Error: Incorrect config in the file '{ini}'.\n"
            "Please fix or remove the config and re-run the script.")
        sys.exit(1)

    sections = config.sections()
    args, displays = [], []
    for section in sections:
        for key, value in config.items(section):
            args.append(f'-{key}={value}')
            displays.append(f'{key} = {value}')

    set_options_by_args(args, displays, ini)

def set_initial_options():
    set_locale()
    set_options_by_config()

    args = list(sys.argv[1:])
    set_options_by_args(args, args)

    if not manager.is_option_set('start_dir'):
        manager.set_option('start_dir', os.getcwd())

    if not manager.is_option_set('save_dir'):
        manager.set_option('save_dir', manager.get_option('start_dir'))

def set_options_by_splitted_params(tids):
    p = splitted.params

    if p.is_splitted:
        specials = []

        if len(tids) > 1:
            specials.extend(['--video-tracks', f'{p.tid}'])

        if all(not p.uids[ind] for ind in p.indexes):
            p.segments_vid = [p.base_video]

            str_times = ''
            for times in p.segments_times:
                start = type_convert.timedelta_to_str(
                    times[0], hours_place=2, decimal_place=6)
                end = type_convert.timedelta_to_str(times[1], 2, 6)

                if str_times:
                    str_times += f',+{start}-{end}'
                else:
                    f'{start}-{end}'

            specials.extend(['--split', f'parts:{str_times}'])

        else:
            p.extracted_orig = True

        if specials:
            manager.set_target_option(p.base_video, 'specials', specials)

    if (p.extracted_orig or
        (len(p.segments_vid) > 1 and
         manager.get_merge_flag('force_retiming'))
        ):
        p.extracted_orig = merge.params.extracted_orig = True
