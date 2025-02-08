import options.manager
import file_info.encoding
from . import params, set_params

def get_common_part_command():
    part = []

    for flg in ['video', 'global_tags', 'chapters']:
        if not options.manager.get_merge_flag(flg):
            part.append(f"--no-{flg.replace('_', '-')}")

    return part + options.manager.get_merge_target_option('specials')

def get_part_command_for_video():
    part = []
    params.fpath, params.fgroup = params.base_video, 'video'

    if params.replace_audio or params.extracted_orig:
        part.append('--no-audio')
    if params.replace_subtitles or params.extracted_orig:
        part.append('--no-subtitles')
    if params.orig_fonts_list or params.replace_fonts:
        part.append('--no-attachments')

    return part + get_common_part_command()

def get_part_command_for_file():
    part = []
    flg = options.manager.get_merge_flag

    if not flg('audio'):
        part.append('--no-audio')
    if not flg('subtitles'):
        part.append('--no-subtitles')
    if not flg('fonts'):
        part.append('--no-attachments')

    return part + get_common_part_command()

def get_params_to_set_fde(key):
    if (params.tgroup == 'signs' and
        key == 'forced' and
        options.manager.get_merge_flag('forced_signs')
        ):
        limit = options.manager.get_option('lim_forced_signs')
    else:
        limit = options.manager.get_option(f'lim_{key}_ttype')

    counters = params.counters_fde_flags.setdefault(key, {})
    count = counters.setdefault(params.tgroup, 0)

    strict = 1 if key == 'forced' else 0
    setted_true = options.manager.get_merge_option(key)

    return limit, counters, count, strict, setted_true

def get_value_forced_default_enabled(key, track_info):
    limit, counters, count, strict, setted_true = get_params_to_set_fde(key)

    if count >= limit:
        value = 0
    elif setted_true:
        value = 1
    elif (key == 'forced' and
          params.tgroup == 'signs'
          ):
        value = 1
    elif (key == 'default' and
          params.tgroup == 'subtitles' and
          (params.default_locale_audio or
           params.setted_false_enabled_subtitles or
           track_info.get('tlang', '') in params.langs_default_audio
           )
          ):
        params.setted_false_enabled_subtitles = True
        value = 0
    elif (setted_true is None and
          not strict and
          options.manager.get_merge_flag(key)
          ):
        value = 1
    else:
        value = 0

    if value:
        counters[params.tgroup] += 1

        if params.tgroup == 'audio' and key == 'default':
            tlang = track_info.get('tlang', '')
            params.langs_default_audio.add(tlang)
            if tlang == params.locale:
                params.default_locale_audio = True

    return '' if value else ':0'

def set_tids_options_pcommand():
    set_params.init_fde_flags_params()
    track_orders = file_info.setted.info['track_orders']

    for params.tgroup in track_orders:
        for fid, tid in track_orders[params.tgroup]:
            part = []

            fpath = params.fpath = file_info.setted.info['file_paths'][fid]
            fgroup = file_info.setted.info[fpath]['file_group']
            params.fgroup = fgroup

            track_info = file_info.setted.info.get(fpath, {}).get(tid, {})
            flg = options.manager.get_merge_flag

            if flg('forceds'):
                val = get_value_forced_default_enabled('forced', track_info)
                part.extend(['--forced-display-flag', f'{tid}{val}'])

            if flg('defaults'):
                val = get_value_forced_default_enabled('default', track_info)
                part.extend(['--default-track-flag', f'{tid}{val}'])

            if flg('enableds'):
                val = get_value_forced_default_enabled('enabled', track_info)
                part.extend(['--track-enabled-flag', f'{tid}{val}'])

            if fgroup != 'video':
                if flg('tnames'):
                    val = track_info.get('tname', '')
                    if val:
                        part.extend(['--track-name', f'{tid}:{val}'])

                if flg('tlangs'):
                    val = track_info.get('tlang', '')
                    if val:
                        part.extend(['--language', f'{tid}:{val}'])

            if (params.tgroup in {'signs', 'subtitles'} and
                flg('sub_charsets')
                ):
                part.extend(file_info.encoding.get_sub_charset_pcommand(
                    fpath, tid))

            cmd = params.command_parts[fid]['cmd']
            p = params.command_parts[fid]['position_to_insert']
            cmd[p:p] = part
            params.command_parts[fid]['position_to_insert'] += len(part)

def get_merge_command():
    command = ['mkvmerge', '-o', params.out_file]

    if options.manager.get_merge_flag('t_orders', params.base_video, 'video'):
        order = file_info.setted.info['track_order_str']
        command.extend(['--track-order', order])

    fid = 0
    cmd = set_params.init_fid_part_cmd(fid)
    part = get_part_command_for_video()

    cmd.extend(part + [params.video_list[0]])
    for part_video in params.video_list[1:]:
        cmd.extend(part + [f'+{part_video}'])

    for params.fgroup in ('audio', 'signs', 'subtitles'):
        fpaths = file_info.setted.info.get('file_groups', {}).get(
            params.fgroup, [])

        for fid, params.fpath in enumerate(fpaths, start=fid+1):
            cmd = set_params.init_fid_part_cmd(fid)
            cmd.extend(get_part_command_for_file() + [params.fpath])

    set_tids_options_pcommand()

    for fid in range(len(params.command_parts)):
        command.extend(params.command_parts[fid]['cmd'])

    for font in params.fonts_list:
        specials = options.manager.get_merge_target_option(
            'specials', font, 'fonts')
        command.extend(specials + ['--attach-file', font])

    if params.new_chapters:
        command.extend(['--chapters', params.new_chapters])

    return command
