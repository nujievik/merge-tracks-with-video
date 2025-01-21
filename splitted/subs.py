from pathlib import Path
from datetime import timedelta

import type_convert
import file_info.mkvtools
from . import common, params
from files.files import EXTENSIONS

def write_subs_segment_lines(file, lines):
    for line in lines:
        if line.startswith('Dialogue:'):
            parts = line.split(',')
            start = type_convert.str_to_timedelta(parts[1].strip())
            end = type_convert.str_to_timedelta(parts[2].strip())

            if start < params.start and end < params.start or start > params.end and end > params.end:
                continue #skip non-segment lines

            else: #retime and write
                new_start = type_convert.timedelta_to_str(start + params.offset)
                new_end = type_convert.timedelta_to_str(end + params.offset)

                line = f"{parts[0]},{new_start},{new_end},{','.join(parts[3:])}"
                file.write(line)

def set_retimed_orig_subs():
    lines = {}

    for ind in params.indexes:
        if lines.get(params.uids[ind], []):
            continue

        params.source = params.sources[ind]
        params.segment = Path(params.temp_dir) / 'orig_subs' / f'subs_{params.subs_cnt}_segment_{ind}.ass'

        common.extract_track()
        with open(params.segment, 'r', encoding='utf-8') as file:
            lines[params.uids[ind]] = file.readlines()

    params.retimed = Path(params.segment.parent) / f'subs_{params.subs_cnt}.ass'

    with open(params.retimed, 'w', encoding='utf-8') as file:
        for line in lines[params.uids[params.indexes[0]]]:
            if line.startswith('Dialogue:'):
                break

            file.write(line) #save lines before dialogues

        for ind in params.indexes:
            params.ind = ind
            lengths = common.get_uid_lengths()

            params.offset = lengths['nonuid']['defacto'] + lengths['uid']['offset'] - params.offsets_start[ind]
            params.start = params.starts[ind]
            params.end = params.ends[ind]

            write_subs_segment_lines(file, lines[params.uids[ind]])

def set_retimed_ext_subs(source):
    params.retimed = Path(params.temp_dir) / 'ext_subs' / source.parent.name / f'subs_{params.subs_cnt}.ass'

    if params.tid is None:
        params.retimed.parent.mkdir(parents=True, exist_ok=True)
        read = source
    else:
        params.source = source
        common.extract_track()
        read = params.retimed

    with open(read, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(params.retimed, 'w', encoding='utf-8') as file:
        for line in lines:
            if line.startswith('Dialogue:'):
                break

            file.write(line) #save lines before dialogues

        for ind in params.indexes:
            params.ind = ind
            lengths = common.get_uid_lengths()

            params.offset = lengths['nonuid']['offset'] + lengths['uid']['offset'] - params.offsets_start[ind]
            params.start = params.starts[ind] + lengths['nonuid']['chapters']
            params.end = params.ends[ind] + lengths['nonuid']['chapters']

            write_subs_segment_lines(file, lines)

def fill_retimed_subs():
    params.retimed_subs[:] = []
    temp = []

    if params.orig_subs and params.extracted_orig:
        for tid in file_info.mkvtools.get_track_type_tids(params.video, 'subtitles (SubStationAlpha)'):
            temp.append([params.video, 'video', tid])

    for source in params.subs_list:
        tids = []

        if source.suffix in EXTENSIONS['retime_subs']:
            temp.append([source, 'subs', None])

        elif source.suffix in EXTENSIONS['mkvtools_supported']:
            for tid in file_info.mkvtools.get_track_type_tids(source, 'subtitles (SubStationAlpha)'):
                temp.append([source, 'subs', tid])

        else:
            print(f"Skip subtitles file '{str(source)}'! \nThese subtitles need to be retimed because"
                  " the video file is splitted. Retime is only possible for SubStationAlpha tracks (.ass).")

    for params.subs_cnt, tmp in enumerate(temp):
        source, filegroup, params.tid = tmp

        set_retimed_orig_subs() if filegroup == 'video' else set_retimed_ext_subs(source)

        params.retimed_subs.append(params.retimed)
        common.set_matching_keys(source, filegroup)
