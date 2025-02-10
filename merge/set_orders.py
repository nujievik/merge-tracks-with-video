import os

from . import params
import options.manager
import file_info.signs
import file_info.setted
import file_info.track_lang
import file_info.track_name
import file_info.by_mkvtools

def init_fpath_tgroup_tids(fpath):
    for tgroup in {'video', 'audio', 'signs', 'subtitles'}:
        file_info.setted.info.setdefault(fpath, {})[tgroup] = []

def set_tid_info(fpath, fgroup, tid, tgroup):
    t_info = file_info.setted.info.setdefault(fpath, {}).setdefault(tid, {})
    args = (params.tid, params.fpath, params.fgroup, params.base_video)

    tname = t_info['tname'] = file_info.track_name.get_track_name(*args)
    t_info['tlang'] = file_info.track_lang.get_track_lang(*args, tname)

    if (tgroup == 'subtitles' and
        file_info.signs.is_signs(fpath, params.base_video, tname)
        ):
        tgroup = 'signs'
        if fgroup == 'subtitles':
            fgroup = 'signs'
            file_info.setted.info[fpath]['file_group'] = fgroup

    return fgroup, tgroup

def set_files_info(fpaths=[], init_tgroups=[]):
    temp_file_groups = {}
    track_groups = file_info.setted.info['track_groups'] = {}

    if not fpaths:
        fpaths = ([params.base_video]
                  + params.audio_list
                  + params.subtitles_list)

    for fpath in fpaths:
        init_fpath_tgroup_tids(fpath)
        fgroup = file_info.by_mkvtools.get_file_group(fpath)

        if init_tgroups:
            tgroups = init_tgroups
        # If audio and subtitles was extracted, skip these groups
        elif fgroup == 'video' and params.extracted_orig:
            tgroups = ['video']
        else:
            tgroups = ['video', 'audio', 'subtitles']

        for tgroup in tgroups:
            for tid in file_info.by_mkvtools.get_track_type_tids(tgroup,
                                                                 fpath):
                # If file was splitted, replace
                params.fpath, params.fgroup, params.tid = (
                    params.matching_keys.get(fpath, (fpath, fgroup, tid)))

                # Set track_name, track_lang and check signs for non-video
                if tgroup != 'video':
                    fgroup, tgroup = set_tid_info(fpath, fgroup, tid, tgroup)

                temp_file_groups.setdefault(fgroup, set()).add(fpath)

                track_groups.setdefault(tgroup, {}).setdefault(
                    fpath, []).append(tid)

                file_info.setted.info[fpath][tgroup].append(tid)

    return temp_file_groups

def get_sort_key(fpath, fgroup, tids=[]):
    opt = options.manager.get_merge_option
    k = (fpath, fgroup)

    f_forced = opt('forced', *k)
    f_default = opt('default', *k)
    f_enabled = opt('enabled', *k)
    flag_order = {True: 0, None: 1, False: 2}

    flag_sort = (flag_order.get(f_forced, 1),
                 flag_order.get(f_default, 1),
                 flag_order.get(f_enabled, 1))

    langs = set()
    for tid in tids:
        lang = file_info.setted.info.get(fpath, {}).get(
            tid, {}).get('tlang', '')
        if lang:
            langs.add(lang)

    if params.locale in langs:
        lang_sort = 0  # Locale first
    elif langs and not langs - {'jpn'}:
        lang_sort = 3  # Jpn latest
    elif langs:
        lang_sort = 2  # Other lang
    else:
        lang_sort = 1  # Undefined lang

    if file_info.setted.info.get(fpath, {}).get('signs', []):
        signs_sort = 0
    else:
        signs_sort = 1

    return (flag_sort[0], flag_sort[1], flag_sort[2], lang_sort, signs_sort)

def set_files_order(temp_file_groups):
    file_paths = file_info.setted.info['file_paths'] = []

    for fgroup in ('video', 'audio', 'signs', 'subtitles'):
        files = sorted(temp_file_groups.get(fgroup, []))  # Sort by name

        sorted_files = sorted(
            files,
            key=lambda fpath: get_sort_key(
                fpath,
                fgroup,
                file_info.setted.info.get(fpath, {}).get(fgroup, [])
            )
        )
        file_groups = file_info.setted.info.setdefault(
            'file_groups', {})[fgroup] = []
        file_groups.extend(sorted_files)
        file_paths.extend(sorted_files)

def set_tracks_order():
    order_str = ''
    track_orders = file_info.setted.info['track_orders'] = {}

    for tgroup in ('video', 'audio', 'signs', 'subtitles'):
        fpaths_with_tids = []

        for fpath in file_info.setted.info['file_paths']:
            fgroup = file_info.setted.info[fpath]['file_group']
            for tid in file_info.setted.info[fpath].get(tgroup, []):
                fpaths_with_tids.append((fpath, fgroup, tid))

        sorted_fpaths_with_tids = sorted(
            fpaths_with_tids,
            key=lambda item: get_sort_key(*item[:2], tids=[item[2]])
        )

        order = []
        for fpath, fgroup, tid in sorted_fpaths_with_tids:
            fid = file_info.setted.info['file_paths'].index(fpath)
            order.append((fid, tid))
            order_str += f'{fid}:{tid},'
            track_orders[tgroup] = tuple(order)

    file_info.setted.info['track_order_str'] = order_str[:-1]

def set_merge_info_orders():
    temp_file_groups = set_files_info()
    set_files_order(temp_file_groups)
    set_tracks_order()
