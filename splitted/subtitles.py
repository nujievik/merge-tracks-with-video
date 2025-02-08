import os
from datetime import timedelta

import type_convert
import file_info.by_mkvtools
from . import common, params
from files.constants import SUFFIXES

def write_subtitles_segment_lines(f, lines):
    for line in lines:
        if line.startswith('Dialogue:'):
            parts = line.split(',')
            start = type_convert.str_to_timedelta(parts[1].strip())
            end = type_convert.str_to_timedelta(parts[2].strip())

            if (start < params.start and end < params.start or
                start > params.end and end > params.end
                ):
                continue  # Skip non-segment lines

            else:  # Retime and write
                new_start = type_convert.timedelta_to_str(
                    start + params.offset)
                new_end = type_convert.timedelta_to_str(end + params.offset)

                line = (f"{parts[0]},{new_start},{new_end},"
                        f"{','.join(parts[3:])}")
                f.write(line)

def set_retimed_orig_subtitles():
    lines = {}

    for ind in params.indexes:
        if lines.get(params.uids[ind], []):
            continue

        source = params.sources[ind]
        segment = os.path.join(
            params.temp_dir, 'orig_subtitles',
            f'subtitles_{params.subtitles_cnt}_segment_{ind}.ass')

        common.extract_track(source, segment)
        with open(segment, 'r', encoding='utf-8') as f:
            lines[params.uids[ind]] = f.readlines()

    params.retimed = os.path.join(
        os.path.dirname(segment), f'subtitles_{params.subtitles_cnt}.ass')

    with open(params.retimed, 'w', encoding='utf-8') as f:
        for line in lines[params.uids[params.indexes[0]]]:
            if line.startswith('Dialogue:'):
                break

            f.write(line)  # Save lines before dialogues

        for ind in params.indexes:
            params.ind = ind
            lengths = common.get_uid_lengths()

            params.offset = (lengths['nonuid']['defacto']
                             + lengths['uid']['offset']
                             - params.offsets_start[ind])
            params.start = params.starts[ind]
            params.end = params.ends[ind]

            write_subtitles_segment_lines(f, lines[params.uids[ind]])

def set_retimed_ext_subtitles(source):
    params.retimed = os.path.join(
        params.temp_dir, 'ext_subtitles',
        os.path.basename(os.path.dirname(source)),
        f'subtitles_{params.subtitles_cnt}.ass')

    if params.tid is None:
        parent_dir = os.path.dirname(params.retimed)
        os.makedirs(parent_dir, exist_ok=True)
        read = source
    else:
        common.extract_track(source, params.retimed)
        read = params.retimed

    with open(read, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(params.retimed, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('Dialogue:'):
                break

            f.write(line)  # Save lines before dialogues

        for ind in params.indexes:
            params.ind = ind
            lengths = common.get_uid_lengths()

            params.offset = (lengths['nonuid']['offset']
                             + lengths['uid']['offset']
                             - params.offsets_start[ind])
            params.start = params.starts[ind] + lengths['nonuid']['chapters']
            params.end = params.ends[ind] + lengths['nonuid']['chapters']

            write_subtitles_segment_lines(f, lines)

def fill_retimed_subtitles():
    params.retimed_subtitles[:] = []
    temp = []

    if params.orig_subtitles and params.extracted_orig:
        for tid in (file_info.by_mkvtools.get_track_type_tids(
            'subtitles (SubStationAlpha)', params.base_video)
        ):
            temp.append((params.base_video, 'video', tid))

    for source in params.subtitles_list:
        tids = []

        if source.endswith(SUFFIXES['retime_subtitles']):
            temp.append((source, 'subtitles', None))

        elif source.endswith(SUFFIXES['mkvtools_supported']):
            for tid in (file_info.by_mkvtools.get_track_type_tids(
                'subtitles (SubStationAlpha)', source)
            ):
                temp.append((source, 'subtitles', tid))

        else:
            print(f"Skip subtitles file '{source}'! \nThese subtitles need "
                  "to be retimed because the video file is splitted. Retime "
                  "is only possible for SubStationAlpha tracks (.ass).")

    for params.subtitles_cnt, tmp in enumerate(temp):
        source, filegroup, params.tid = tmp

        if filegroup == 'video':
            set_retimed_orig_subtitles()
        else:
            set_retimed_ext_subtitles(source)

        params.retimed_subtitles.append(params.retimed)
        common.set_matching_keys(source, filegroup)
