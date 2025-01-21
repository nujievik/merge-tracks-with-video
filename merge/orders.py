import flags.merge
from . import params
from file_info import mkvtools, signs, track_lang, track_name

def get_f_t_groups(ind, filegroup='', trackgroups=[]):
    if not filegroup:
        if ind < 1:
            filegroup = 'video'
        elif ind < 1 + len(params.audio_list):
            filegroup = 'audio'
        else:
            filegroup = 'subs'

    if not trackgroups:
        if filegroup == 'video' and params.extracted_orig:
            trackgroups = ['video']
        else:
            trackgroups = ['video', 'audio', 'subs']

    return filegroup, trackgroups


def set_files_info(filepaths=[], filegroup='', trackgroups=[]):
    tmp_info = {}
    init_fgroup, init_tgroups = filegroup, trackgroups
    filepaths = filepaths if filepaths else [params.video] + params.audio_list + params.subs_list

    for ind, filepath in enumerate(filepaths):
        filegroup, trackgroups = get_f_t_groups(ind, init_fgroup, init_tgroups)

        for trackgroup in trackgroups:
            for tid in mkvtools.get_track_type_tids(filepath, trackgroup):
                params.filepath, params.filegroup, params.tid = params.matching_keys.get(str(filepath), [filepath, filegroup, tid])

                if trackgroup != 'video':
                    args = [params.tid, params.filepath, params.filegroup, params.video]
                    tname = track_name.get_track_name(*args)
                    tlang = track_lang.get_track_lang(*args, tname)

                    params.info.setdefault(str(filepath), {}).setdefault(tid, {})['tname'] = tname
                    params.info.setdefault(str(filepath), {}).setdefault(tid, {})['tlang'] = tlang

                    if trackgroup == 'subs' and signs.is_signs(params.video, filepath, tname):
                        trackgroup = 'signs'

                params.info.setdefault(str(filepath), {}).setdefault(trackgroup, []).append(tid)
                params.info.setdefault('trackgroup', {}).setdefault(trackgroup, {}).setdefault(str(filepath), []).append(tid)

                if trackgroup == 'signs' and filegroup == 'subs':
                    filegroup = 'signs'

                params.info[str(filepath)]['filegroup'] = filegroup
                if not filepath in tmp_info.setdefault('filegroup', {}).setdefault(filegroup, []):
                    tmp_info['filegroup'][filegroup].append(filepath)

    return tmp_info

def get_sort_key(filepath, filegroup, tids=[]):
    flag = flags.merge.flag
    k = [filepath, filegroup]

    f_force = flag('forced', *k)
    f_default = flag('default', *k)
    f_enabled = flag('enabled', *k)
    flag_order = {True: 0, None: 1, False: 2}

    flag_sort = (flag_order.get(f_force, 1), flag_order.get(f_default, 1), flag_order.get(f_enabled, 1))

    langs = set()
    for tid in tids:
        if params.info.get(str(filepath), {}).get(tid, {}).get('tlang', ''):
            langs.add(params.info[str(filepath)][tid]['tlang'])

    if params.locale in langs:
        lang_sort = 0  # locale first
    elif langs and not langs - {'jpn'}:
        lang_sort = 3  # 'jpn' latest
    elif langs:
        lang_sort = 2  # other lang
    else:
        lang_sort = 1  # undefined lang

    signs_sort = 0 if params.info.get(str(filepath), {}).get('signs', []) else 1

    return (flag_sort[0], flag_sort[1], flag_sort[2], lang_sort, signs_sort)

def set_files_order(tmp_info):
    for filegroup in ['video', 'audio', 'signs', 'subs']:
        sorted_files = sorted(
            tmp_info['filegroup'].get(filegroup, []),
            key=lambda filepath: get_sort_key(filepath, filegroup, params.info.get(str(filepath), {}).get(filegroup, []))
        )
        params.info.setdefault('filegroup', {}).setdefault(filegroup, []).extend(sorted_files)
        params.info.setdefault('filepaths', []).extend(sorted_files)

def set_tracks_order():
    order_str = ''
    for trackgroup in ['video', 'audio', 'signs', 'subs']:
        tids_with_filepaths = []

        for filepath in params.info['filepaths']:
            filegroup = params.info[str(filepath)]['filegroup']
            for tid in params.info.get(str(filepath), {}).get(trackgroup, []):
                tids_with_filepaths.append((filepath, filegroup, tid))

        sorted_tids_with_filepaths = sorted(
            tids_with_filepaths,
            key=lambda item: get_sort_key(*item[:2], tids=[item[2]])
        )

        order = []
        for filepath, filegroup, tid in sorted_tids_with_filepaths:
            fid = params.info['filepaths'].index(filepath)
            order.append((fid, tid))
            order_str += f'{fid}:{tid},'
            params.info.setdefault('t_order', {})[trackgroup] = tuple(order)

    params.info['t_order']['all_str'] = order_str[:-1]

def set_merge_info_orders():
    tmp_info = set_files_info()
    set_files_order(tmp_info)
    set_tracks_order()
