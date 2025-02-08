import re
from datetime import timedelta

import executor
import type_convert
import merge.params
from . import params
import options.manager
import file_info.by_mkvtools
from options.values import MATCHINGS

def add_skips(linking=False):
    names = set()

    for flg in ['opening', 'ending']:
        if not options.manager.get_merge_flag(flg):
            names.add(flg)

            for flg_short, flg_long in MATCHINGS['full'].items():
                if flg_long == flg:
                    names.add(flg_short)

    rm_chapters = options.manager.get_option('rm_chapters')
    names.update({name.lower() for name in rm_chapters})

    rm_linking = linking or not options.manager.get_merge_flag('linking')

    for ind, name in enumerate(params.names):
        uid = params.uids[ind]
        if (name.lower() in names or
            rm_linking and uid or
            uid in params.segments.get('skips_uid', set())
            ):
            params.skips.add(ind)

def get_split_command():
    command = [
        'mkvmerge', '-o', params.segment, '--split',
        f'parts:{params.start}-{params.end}', '--no-chapters',
        '--no-global-tags', '--no-subtitles', f'--{params.file_type}-tracks',
        f'{params.tid}'
    ]
    if params.file_type == 'video':
        command.append('--no-audio')
    else:
        command.append('--no-video')
    if not merge.params.orig_fonts:
        command.append('--no-attachments')
    command.append(params.source)

    return command

def set_segment_info(mkvmerge_stdout):
    duration = None
    timestamps = re.findall(
        r'Timestamp used in split decision: (\d{2}:\d{2}:\d{2}\.\d{9})',
        mkvmerge_stdout)

    if len(timestamps) == 2:
        params.defacto_start = type_convert.str_to_timedelta(timestamps[0])
        params.defacto_end = type_convert.str_to_timedelta(timestamps[1])

    elif len(timestamps) == 1:
        timestamp = type_convert.str_to_timedelta(timestamps[0])

        if params.start > timedelta(0):  # Timestamp for start
            params.defacto_start = timestamp
            duration = file_info.by_mkvtools.get_info_by_query(
                'Duration:', params.segment)
            params.defacto_end = params.defacto_start + duration

        else:
            params.defacto_start = timedelta(0)
            params.defacto_end = timestamp

    else:
        params.defacto_start = timedelta(0)
        duration = file_info.by_mkvtools.get_info_by_query(
            'Duration:', params.segment)
        params.defacto_end = duration

    # Real playback <= track duration
    if duration and params.defacto_end <= params.end:
        params.offset_end = timedelta(0)
    else:
        params.offset_end = params.defacto_end - params.end

    params.offset_start = params.defacto_start - params.start
    params.length = params.defacto_end - params.defacto_start

def split_file(repeat=True):
    command = get_split_command()

    if options.manager.get_merge_flag('verbose'):
        print(f"Extracting a segment of the {params.file_type} track from "
              f"the file '{params.source}'. Executing the following command:"
              f"\n{type_convert.command_to_print_str(command)}")

    set_segment_info(executor.execute(command))

    if (repeat and
        any(td > params.ACCEPT_OFFSETS[params.file_type]
            for td in [params.offset_start, params.offset_end])
        ):
        old_start = params.start
        old_end = params.defacto_end - params.offset_end

        if params.start - params.offset_start > timedelta(0):
            params.start = params.start - params.offset_start
        params.end = params.end - params.offset_end

        split_file(repeat=False)
        params.offset_start = params.defacto_start - old_start
        params.offset_end = params.defacto_end - old_end

def merge_file_segments(segments):
    command = ['mkvmerge', '-o', params.retimed]
    command.append(segments[0])
    for segment in segments[1:]:
        command.append(f'+{segment}')

    if options.manager.get_merge_flag('verbose'):
        print(f'Merging retimed {params.file_type} track segments. Executing '
              'the following command:\n'
              f'{type_convert.command_to_print_str(command)}')

    executor.execute(command, get_stdout=False)

def set_matching_keys(filepath, filegroup):
    merge.params.matching_keys[params.retimed] = (
        filepath, filegroup, params.tid)

def get_uid_lengths():
    lengths = {'uid': {'chapters': timedelta(0), 'defacto': timedelta(0)},
               'nonuid': {'chapters': timedelta(0), 'defacto': timedelta(0)}}

    for ind in range(0, params.ind):
        if params.uids[ind] == params.uids[params.ind]:
            key1 = 'uid'
        else:
            key1 = 'nonuid'

        lengths[key1]['chapters'] += (params.chap_ends[ind]
                                      - params.chap_starts[ind])
        if ind in params.indexes:
            lengths[key1]['defacto'] += params.ends[ind] - params.starts[ind]

    for key1 in ['uid', 'nonuid']:
        lengths[key1]['offset'] = (lengths[key1]['defacto']
                                   - lengths[key1]['chapters'])
    return lengths

def extract_track(source, out):
    command = ['mkvextract', 'tracks', source, f'{params.tid}:{out}']

    if options.manager.get_merge_flag('verbose'):
        print(f"Extracting subtitles track {params.tid} from the file "
              f"'{source}'. Executing the following command:\n"
              f"{type_convert.command_to_print_str(command)}")

    executor.execute(command, get_stdout=False)
