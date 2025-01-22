import flags.merge
from . import orders, params
from file_info import encoding_detect

def get_common_part_command():
    part = []

    for key in ['video', 'global_tags', 'chapters']:
        if not flags.merge.bool_flag(key):
            part.append(f"--no-{key.replace('_', '-')}")

    return part + flags.merge.for_flag('options')

def get_part_command_for_video():
    part = []
    params.filepath, params.filegroup = params.video, 'video'

    if params.replace_audio or params.extracted_orig:
        part.append('--no-audio')
    if params.replace_subs or params.extracted_orig:
        part.append('--no-subtitles')
    if params.orig_fonts_list or params.replace_font:
        part.append('--no-attachments')

    return part + get_common_part_command()

def get_part_command_for_file(filepath):
    part = []
    params.filepath = filepath

    if not flags.merge.bool_flag('audio'):
        part.append('--no-audio')
    if not flags.merge.bool_flag('subs'):
        part.append('--no-subtitles')
    if not flags.merge.bool_flag('fonts'):
        part.append('--no-attachments')

    return part + get_common_part_command()

def get_value_force_def_en(key):
    if params.trackgroup == 'signs' and key == 'forced' and flags.merge.bool_flag('forced_signs'):
        lim = flags.merge.get_flag.flag('lim_forced_signs')
    else:
        lim = flags.merge.get_flag.flag(f'lim_{key}_ttype')

    cnt = params.info.setdefault('cnt', {}).setdefault(key, {}).setdefault(params.trackgroup, 0)
    strict = 1 if key == 'forced' else 0
    force = flags.merge.flag(key)

    if cnt >= lim:
        value = 0
    elif force:
        value = 1
    elif key == 'forced' and params.trackgroup == 'signs' and flags.merge.bool_flag('forced_signs'):
        value = 1
    elif key == 'default' and params.trackgroup == 'subs' and (params.info.get('default_locale_audio', False) or params.t_info.get('tlang', '') in params.info.get('langs_default_audio', set())):
        value = 0
    elif force is None and not strict and flags.merge.bool_flag(key):
        value = 1
    else:
        value = 0

    if value:
        params.info['cnt'][key][params.trackgroup] += 1

        if params.trackgroup == 'audio' and key == 'default':
            params.info.setdefault('langs_default_audio', set()).add(params.t_info.get('tlang', ''))

            if params.t_info.get('tlang', '') == params.locale:
                params.info['default_locale_audio'] = True

    return '' if value else ':0'

def set_tids_flags_pcommand():
    for params.trackgroup in ['video', 'audio', 'signs', 'subs']:
        for fid, tid in params.info['t_order'].get(params.trackgroup, ()):
            part = []
            cmd = params.info['cmd'][fid]
            position = params.info.setdefault('position', {}).setdefault(fid, 0)

            filepath = params.filepath = params.info['filepaths'][fid]
            filegroup = params.filegroup = params.info[str(filepath)]['filegroup']

            params.t_info = params.info.get(str(filepath), {}).get(tid, {})
            flg = flags.merge.bool_flag

            if flg('forceds'):
                val = get_value_force_def_en('forced')
                part.extend(['--forced-display-flag', f'{tid}{val}'])

            if flg('defaults'):
                val = get_value_force_def_en('default')
                part.extend(['--default-track-flag', f'{tid}{val}'])

            if flg('enableds'):
                val = get_value_force_def_en('enabled')
                part.extend(['--track-enabled-flag', f'{tid}{val}'])

            if filegroup != 'video':
                if flg('tnames'):
                    val = params.info.get(str(filepath), {}).get(tid, {}).get('tname', '')
                    if val:
                        part.extend(['--track-name', f'{tid}:{val}'])
                if flg('tlangs'):
                    val = params.info.get(str(filepath), {}).get(tid, {}).get('tlang', '')
                    if val:
                        part.extend(['--language', f'{tid}:{val}'])

            if all(x in {'signs', 'subs'} for x in [filegroup, params.trackgroup]):
                if flg('sub_charsets'):
                    part.extend(encoding_detect.get_sub_charset_pcommand(filepath, tid))

            cmd[position:position] = part
            params.info['position'][fid] += len(part)

def get_merge_command():
    params.info = {}
    orders.set_merge_info_orders()

    command = ['mkvmerge', '-o', str(params.output)]

    if flags.merge.bool_flag('t_orders', params.video, 'video'):
        command.extend(['--track-order', params.info['t_order']['all_str']])

    fid = 0
    cmd = params.info.setdefault('cmd', {}).setdefault(fid, [])
    part = get_part_command_for_video()

    cmd.extend(part + [str(params.video_list[0])])
    for video in params.video_list[1:]:
        cmd.extend(part + [f'+{str(video)}'])

    for params.filegroup in ['audio', 'signs', 'subs']:
        filepaths = params.info['filegroup'].get(params.filegroup, [])

        for fid, filepath in enumerate(filepaths, start=fid+1):
            cmd = params.info['cmd'].setdefault(fid, [])
            cmd.extend(get_part_command_for_file(filepath) + [str(filepath)])

    set_tids_flags_pcommand()

    for fid, cmd in params.info['cmd'].items():
        command.extend(cmd)

    for font in params.fonts_list:
        command.extend(flags.merge.for_flag('options', font, 'fonts') + ['--attach-file', str(font)])

    if params.new_chapters:
        command.extend(['--chapters', str(params.new_chapters)])

    return command
