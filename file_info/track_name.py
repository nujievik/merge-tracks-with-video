import path_methods
import options.manager
from . import by_mkvtools, setted

def get_track_name_by_path(fpath, base_video):
    tail = path_methods.get_tail_file_stem(fpath, base_video)

    if len(tail) > 2:
        return tail
    else:
        return path_methods.get_clean_name_file_dir(fpath)

def get_track_name(tid, fpath, fgroup, base_video):
    tid_info = setted.info.setdefault(fpath, {}).setdefault(tid, {})

    if tid_info.get('tname', None) is not None:
        return tid_info['tname']

    if fgroup == 'video':
        tname = by_mkvtools.get_info_by_query('Name:', fpath, tid)

    else:
        tname = options.manager.get_merge_option('tname', fpath, fgroup)
        if not tname:
            tname = by_mkvtools.get_info_by_query('Name:', fpath, tid)
        if not tname:
            tname = get_track_name_by_path(fpath, base_video)

    tid_info['tname'] = tname
    return tname
