import re

import type_convert
import path_methods
from . import manager, values

def get_key_by_arg(arg, target_key):
    key = None

    if not arg.startswith(('-', '+')) and not target_key:
        for opt in ('start_dir', 'save_dir'):
            if not manager.is_option_set(opt):
                key = opt
                break
        return key

    clean_arg = arg.strip('\'"').lstrip('-+')
    index = clean_arg.find('=')
    if index != -1:
        key = clean_arg[:index]
    else:
        key = clean_arg

    while True:
        modified = False
        for find, replace in values.MATCHINGS['part'].items():
            if find in key:
                key = key.replace(find, replace)
                modified = True

        if not modified:
            break

    for find, replace in values.MATCHINGS['full'].items():
        if find == key:
            key = replace
            break

    return key

def get_value_range_option(number, key, value):
    if number:
        num2 = manager.get_option(key)[1]
        value = [number, num2]

    else:
        match = re.search(r'[-:,]', value)
        if match:
            ind = match.start()

            num1 = type_convert.str_to_number(value[:ind], positive=True)
            num2 = type_convert.str_to_number(value[ind+1:], positive=True)
            if num1 is not None and num2 is not None and num2 >= num1:
                pass
            elif num1 is not None:
                num2 = manager.get_option(key)[1]
            elif num2 is not None:
                num1 = manager.get_option(key)[0]

            if num1 is not None:
                value = [num1, num2]
            else:
                value = None

        else:
            value = None

    return value

def get_value_by_arg(arg, key, target_key, target_options):
    value = None

    if not arg.startswith(('-', '+')) and not target_key:
        value = path_methods.path_to_normpath(arg.strip('\'"'))
        return key, value, target_key, target_options

    index = arg.find("=")
    if index != -1:
        value = arg[index + 1:]
        number = type_convert.str_to_number(value)

        if key == 'target':
            if target_key and target_options:
                manager.set_target_option(target_key, 'specials',
                                          target_options)
            str_value = value.strip('\'"')
            if str_value in {'global', ''}:
                target_key = None
            else:
                value = path_methods.path_to_normpath(str_value)
                target_key = value

            target_options = []

        elif key.endswith('dir'):
            value = path_methods.path_to_normpath(value.strip('\'"'))
            if f'save_{key}' in values.DEFAULT:
                key = f'save_{key}'

        elif key in values.TYPES['bool']:
            clean = value.strip('\'"')
            if clean.lower() == 'true':
                value = True
            elif clean.lower() == 'false':
                value = False

        elif key in values.TYPES['str']:
            value = value.strip('\'"')

        elif key in values.TYPES['set']:
            value = set(value.strip('\'"').split(','))

        elif key in values.TYPES['list']:
            value = [item.strip() for item in value.strip('[]').split(',')]

        elif number is not None and key in values.TYPES['limit']:
            value = number

        elif key in values.TYPES['range']:
            value = get_value_range_option(number, key, value)

        else:
            value = None

    elif key in values.TYPES['bool']:
        value = not (arg.startswith('--no') or (
                     arg.startswith('-') and not arg.startswith('--')))

    return key, value, target_key, target_options

def get_key_and_value(arg, target_key, target_options):
    key = get_key_by_arg(arg, target_key)
    return get_value_by_arg(arg, key, target_key, target_options)
