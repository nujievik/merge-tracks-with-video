import os

import merge.params
from .values import DEFAULT, setted, STRICT_BOOL, TYPES

def set_option(key, value, check_exists=True):
    if not check_exists or key in DEFAULT:
        setted[key] = value
    else:
        print(f"Error: option '{key}' not found, option is not set.")

def set_target_option(target_key, key, value):
    if key == 'specials':
        value[0:0] = setted.get('target', {}).get(
            target_key, {}).get('specials', [])
    setted.setdefault('target', {}).setdefault(target_key, {})[key] = value

def get_option(key, default_if_not_set=True):
    value = setted.get(key, None)
    if value is None and default_if_not_set:
        value = DEFAULT.get(key, None)
    return value

def get_target_option(target_key, key):
    return setted.get('target', {}).get(target_key, {}).get(key, None)

def is_option_set(key):
    return False if setted.get(key, None) is None else True

def is_option_or_condition(key, condition):
    val = get_option(key, default_if_not_set=False)
    is_set = is_option_set(key)
    return True if is_set and val or not is_set and condition else False

def get_merge_target_keys(fpath, fgroup, replace_target=True):
    if replace_target:
        fpath = fpath if fpath else merge.params.fpath
        fgroup = fgroup if fgroup else merge.params.fgroup

        fpath, fgroup, _ = merge.params.matching_keys.get(
            fpath, (fpath, fgroup, None))

    return fpath, fgroup

def get_merge_target_option(key, fpath=None, fgroup=None,
                            replace_target=True):
    fpath, fgroup = get_merge_target_keys(fpath, fgroup, replace_target)

    opt = None
    opt_list = []
    targets = [fpath, fgroup, os.path.dirname(fpath)]
    priority = get_option('target_priority')

    if priority == 'file_first':
        for target in targets:
            opt = get_target_option(target, key)
            if opt is not None:
                break

    else:
        for target in reversed(targets):
            opt = get_target_option(target, key)

            if priority == 'dir_first':
                if opt is not None:
                    break
            else:
                opt_list.append(opt)

    # Processing target_priority 'mix'
    if len(opt_list) > 0:
        if key == 'specials':
            opt = [x for x in opt_list if x]

        elif key in TYPES['bool']:
            opt = not False in opt_list

        elif key in TYPES['str']:
            opt = ''.join(x for x in opt_list if x)

    if opt is None and key == 'specials':
        return []
    else:
        return opt

def get_merge_option(key, fpath=None, fgroup=None, replace_target=True):
    fpath, fgroup = get_merge_target_keys(fpath, fgroup, replace_target)

    opt = get_merge_target_option(key, fpath, fgroup, replace_target=False)
    if opt is None:
        opt = get_option(key, default_if_not_set=False)

    return opt

def get_merge_flag(key, fpath=None, fgroup=None, replace_target=True):
    fpath, fgroup = get_merge_target_keys(fpath, fgroup, replace_target)

    flg1 = get_merge_option(key, fpath, fgroup, replace_target=False)
    flg2 = get_option(key, not merge.params.pro)

    for val in (True, False):
        if merge.params.pro and key in STRICT_BOOL[val]:
            if flg1 is val or (flg1 is None and flg2 is val):
                return val
            else:
                return not val

    return False if flg1 is False or (flg1 is None and not flg2) else True
