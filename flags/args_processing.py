import re
import sys
from pathlib import Path

import type_convert
from . import get_flag, set_flag
from .flags import FOR_SEPARATE_FLAGS, MATCHINGS, TYPES

def get_key_by_arg(arg, for_key):
    key = None

    if not arg.startswith(('-', '+')) and not for_key:
        for flg in ['start_dir', 'save_dir']:
            if str(get_flag.flag(flg)) == str(Path.cwd()):
                key = flg
                break
        return key

    clean_arg = arg.strip("'\"").lstrip("-+")
    index = clean_arg.find("=")
    if index != -1:
        key = clean_arg[:index]
    else:
        key = clean_arg

    while True:
        modified = False
        for find, replace in MATCHINGS['part'].items():
            if find in key:
                key = key.replace(find, replace)
                modified = True

        if not modified:
            break

    for find, replace in MATCHINGS['full'].items():
        if find == key:
            key = replace
            break

    return key

def get_value_by_arg(arg, key, for_key, for_key_options):
    value = None

    if not arg.startswith(('-', '+')) and not for_key:
        value = type_convert.str_to_path(arg.strip("'\""))
        return key, value, for_key, for_key_options

    index = arg.find("=")
    if index != -1:
        value = arg[index + 1:]
        number = type_convert.str_to_number(value)

        if key == 'for':
            if for_key and for_key_options:
                set_flag.for_flag(for_key, 'options', for_key_options)

            str_value = value.strip("'\"")
            if str_value in {"all", ""}:
                for_key = None
            else:
                value = type_convert.str_to_path(str_value)
                for_key = str(value)

            for_key_options = []

        elif {key, f'save_{key}'} & TYPES['path']:
            value = type_convert.str_to_path(value.strip("'\""))
            if f'save_{key}' in TYPES['path']:
                key = f'save_{key}'

        elif key in TYPES['bool']:
            clean = value.strip("'\"")
            value = True if clean.lower() == 'true' else False if clean.lower() == 'false' else None

        elif key in TYPES['str']:
            value = value.strip("'\"")

        elif key in TYPES['set']:
            value = set(value.strip("'\"").split(','))

        elif key in TYPES['list']:
            value = [item.strip() for item in value.strip('[]').split(',')]

        elif number is not None and key in TYPES['limit']:
            value = number

        elif number and key in TYPES['range']: #range start with 1, not 0
            num2 = get_flag.flag(key)[1]
            value = [number, num2]

        elif key in TYPES['range']:
            match = re.search(r'[-:,]', value)
            if match:
                ind = match.start()

                num1 = type_convert.str_to_number(value[:ind], positive=True)
                num2 = type_convert.str_to_number(value[ind + 1:], positive=True)

                if num1 is not None and num2 is not None and num2 >= num1:
                    pass
                elif num1 is not None:
                    num2 = get_flag.flag(key)[1]
                elif num2 is not None:
                    num1 = get_flag.flag(key)[0]

                if num1 is not None:
                    value = [num1, num2]
                else:
                    value = None

            else:
                value = None

        else:
            value = None

    elif key in TYPES['bool']:
        value = not (arg.startswith('--no') or (arg.startswith('-') and not arg.startswith('--')))

    return key, value, for_key, for_key_options

def processing_for_arg(arg, key, value, for_key, for_key_options):
    setted = False

    if key == 'for':
        setted = True

    elif for_key:
        if key in FOR_SEPARATE_FLAGS and value is not None:
            set_flag.for_flag(for_key, key, value)
        else:
            for_key_options.append(arg.strip("'\""))
        setted = True

    return key, value, for_key, for_key_options, setted

def set_flags_by_args(args, displays, config=None):
    for_key = None
    for_key_options = []
    add_msg = f" in the config file '{config}'" if config else ''

    for ind, arg in enumerate(args):
        key = get_key_by_arg(arg, for_key)

        r = get_value_by_arg(arg, key, for_key, for_key_options)
        r = processing_for_arg(arg, *r)

        key, value, for_key, for_key_options, setted = r
        if setted:
            continue

        if key and value is not None:
            set_flag.flag(key, value)
        else:
            print(f"Error: unrecognized argument '{displays[ind]}'{add_msg}. \nPlease fix it and re-run the script.")
            sys.exit(1)

    if for_key and for_key_options:
        set_flag.for_flag(for_key, 'options', for_key_options)
