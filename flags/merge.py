from . import get_flag
from merge import params
from .flags import DEFAULT, flags, STRICT_BOOL, TYPES

def replace_keys(fpath, fgroup, replace=True):
    if replace:
        fpath = fpath if fpath else params.filepath
        fgroup = fgroup if fgroup else params.filegroup

        fpath, fgroup, _ = params.matching_keys.get(str(fpath), [fpath, fgroup, None])

    return fpath, fgroup

def for_flag(key3, fpath=None, fgroup=None, replace=True):
    flag = None
    flag_list = []
    fpath, fgroup = replace_keys(fpath, fgroup)
    keys2 = [str(fpath), fgroup, str(fpath.parent)]

    if get_flag.flag('for_priority') == 'file_first':
        for key2 in keys2:
            flag = get_flag.for_flag(key2, key3)
            if flag is not None:
                break

    else:
        for key2 in reversed(keys2):
            if get_flag.flag('for_priority') == 'dir_first':
                flag = get_flag.for_flag(key2, key3)
                if flag is not None:
                    break

            else:
                flag_list.append(get_flag.for_flag(key2, key3))

    if len(flag_list) > 0:
        if key3 == 'options':
            temp = []
            for flg in flag_list:
                if flg:
                    temp.append(flg)

            if temp:
                flag = temp

        elif key3 in TYPES['bool']:
            flag = not False in flag_list

        elif key3 in TYPES['str']:
            flag = ''
            for flg in flag_list:
                if flg:
                    flag += flg

    if flag is None and key3 == 'options':
        return []
    return flag

def flag(key, fpath=None, fgroup=None, replace=True, default_if_missing=False):
    fpath, fgroup = replace_keys(fpath, fgroup, replace)

    flag = for_flag(key, fpath, fgroup, replace=False)
    if flag is None:
        flag = get_flag.flag(key, default_if_missing=default_if_missing)

    return flag

def bool_flag(key, fpath=None, fgroup=None, replace=True):
    fpath, fgroup = replace_keys(fpath, fgroup, replace)

    flg1 = flag(key, fpath, fgroup, replace=False)
    flg2 = get_flag.flag(key, not params.pro)

    for val in [True, False]:
        if params.pro and key in STRICT_BOOL.get(val, {}):
            return val if flg1 is val or (flg1 is None and flg2 is val) else not val
    return False if flg1 is False or (flg1 is None and not flg2) else True
