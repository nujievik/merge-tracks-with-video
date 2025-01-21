from pathlib import Path
from datetime import timedelta

import file_info.mkvtools
from . import common, params

def get_segments_orig_audio():
    segments, lengths = [], {}

    for ind in params.indexes:
        params.start, params.end = params.starts[ind], params.ends[ind]
        offset = lengths.setdefault('audio', timedelta(0)) - lengths.setdefault('video', timedelta(0))
        params.start = params.start + offset if params.start + offset >= timedelta(0) else params.start

        params.segment = Path(params.temp_dir) / 'orig_audio' / f'audio_{params.audio_cnt}_segment_{ind}.mka'
        params.source = params.sources[ind]

        common.split_file()
        segments.append(params.segment)

        lengths['video'] += params.lengths[ind]
        lengths['audio'] += params.length

    return segments

def get_segments_ext_audio():
    segments, lengths = [], {}

    for params.ind in params.indexes:
        nonuid_length = common.get_uid_lengths()['nonuid']['chapters']
        offset = lengths.setdefault('audio', timedelta(0)) - lengths.setdefault('video', timedelta(0))

        if params.starts[params.ind] + nonuid_length + offset >= timedelta(0):
            params.start = params.starts[params.ind] + nonuid_length + offset
        else:
            params.start = params.starts[params.ind] + nonuid_length

        params.end = params.ends[params.ind] + nonuid_length
        params.segment = (Path(params.temp_dir) / 'ext_audio' / params.source.parent.name /
                          f'audio_{params.audio_cnt}_segment_{params.ind}.mka')

        common.split_file()
        segments.append(params.segment)

        lengths['video'] += params.lengths[params.ind]
        lengths['audio'] += params.length

    return segments

def fill_retimed_audio():
    params.retimed_audio[:] = []
    params.file_type = 'audio'
    temp = []

    if params.orig_audio and params.extracted_orig:
        for tid in file_info.mkvtools.get_track_type_tids(params.video, 'audio'):
            temp.append([params.video, 'video', tid])

    for source in params.audio_list:
        for tid in file_info.mkvtools.get_track_type_tids(source, 'audio'):
            temp.append([source, 'audio', tid])

    for params.audio_cnt, tmp in enumerate(temp):
        params.source, filepath, filegroup, params.tid = tmp[0], *tmp
        segments = get_segments_orig_audio() if filegroup == 'video' else get_segments_ext_audio()

        params.retimed = Path(params.segment.parent) / f'audio_{params.audio_cnt}.mka'
        common.merge_file_segments(segments)

        params.retimed_audio.append(params.retimed)
        common.set_matching_keys(filepath, filegroup)
