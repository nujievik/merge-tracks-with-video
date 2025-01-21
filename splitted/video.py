from pathlib import Path
from datetime import timedelta

import executor
import files.find_ext
import file_info.mkvtools
import flags.set_splitted
from . import common, params
from file_info import duration, i_frames

def set_video_source(exit_if_none=False):
    params.uid_info = params.segments.setdefault(params.uid, {})

    if not params.uid:
        params.source = params.video
    else:
        params.source = params.uid_info.get('source', None)

        if not params.source:
            for video in reversed(files.find_ext.find_ext_files(params.video.parent, '.mkv')):
                if file_info.mkvtools.get_file_info(video, 'Segment UID:').lower() == params.uid:
                    params.source = params.uid_info['source'] = video
                    break

    if params.source:
        return params.source

    msg_tail = '. Please move this file to the video directory and re-run the script.' if exit_if_none else ' and has been skipped.'
    print(f"Video file with UID '{params.uid}' not found in the video directory '{str(params.video.parent)}'."
          f"\nThis file is a segment of the linked video '{str(params.video)}'{msg_tail}")

    if exit_if_none:
        executor.remove_temp_files()

    else: #add all uid segments in skips
        for ind, uid in enumerate(params.uids[params.ind:], start=params.ind):
            if uid == params.uid:
                params.skips.add(ind)
            params.segments.setdefault('skips_uid', set()).add(params.uid)

def set_video_ind_end():
    for ind, uid in enumerate(params.uids[params.ind:], start=params.ind):

        if uid == params.uid and ind not in params.skips:
            params.ind_end = ind

        elif uid == params.uid:
            params.splitted = True
            break

        elif uid != params.uid and ind not in params.skips:
            if not params.splitted:
                for uid in params.uids[ind:]:
                    if uid == params.uid:
                        params.splitted = True
                        break
            break

def set_video_split_times():
    params.start = params.end = None
    set_video_ind_end()
    start, end = params.chap_starts[params.ind], params.chap_ends[params.ind_end]

    if start + abs(end - duration.get_duration('video')) < params.strict:
        return True

    elif not params.uid and params.uid_info.get('end', None) and abs(start - params.uid_info['end']) < params.strict:
        params.start = params.uid_info['end']

    for ind, td in enumerate([start, end]):
        if not ind and params.start is not None:
            continue

        times = i_frames.get_times_i_frames(td, '0.000001')
        times.append(params.uid_info['duration']['video'])
        times.extend(i_frames.get_times_i_frames(td, 2*(td - times[0])))

        offset = timedelta(seconds=99999)
        for t in times:
            if abs(td - t) < offset:
                time, offset = t, abs(td - t)

        if not ind:
            params.start = time
        else:
            params.end = time

    if not params.uid:
        params.uid_info['end'] = params.end

def set_video_segment_td():
    params.segment = Path(params.temp_dir) / f'video_segment_{params.ind}_{params.uid}.mkv'
    info = params.segments.setdefault(params.segment, {}) if params.uid else {}

    if set_video_split_times():
        params.defacto_start, params.defacto_end = timedelta(0), duration.get_duration('video')
        params.segment = params.source

    elif info.get('end', None) and abs(info['start'] - params.start) + abs(info['end'] - params.end) < params.strict:
        params.defacto_start, params.defacto_end = info['start'], info['end']

    elif all(not params.uids[ind] or params.uids[ind] in params.skips for ind in range(0, len(params.uids))):
        params.defacto_start, params.defacto_end = params.start, params.end
        params.segment = params.source

    else:
        common.split_file(repeat=False)
        if params.uid:
            info['start'], info['end'] = params.defacto_start, params.defacto_end

def set_video_segment_info():
    set_video_segment_td()

    params.segments_vid.append(params.segment)
    params.segments_times.append([params.defacto_start, params.defacto_end])
    params.segments_inds.setdefault(str(params.segment), set()).update({params.ind, params.ind_end})

    for ind in range(params.ind, params.ind_end + 1):
        if ind in params.skips:
            continue

        params.indexes.append(ind)
        params.sources[ind] = params.source

        if ind == params.ind:
            params.starts[ind] = params.defacto_start
            params.offsets_start[ind] = params.defacto_start - params.chap_starts[ind]

        else:
            params.offsets_start[ind] = timedelta(0)

        if ind == params.ind_end:
            params.ends[ind] = params.defacto_end
            params.offsets_end[ind] = params.defacto_end - params.chap_ends[ind]

        else:
            for temp_ind, uid in enumerate(params.uids[ind+1:]):
                if uid == params.uid:
                    next_uid_start = params.chap_starts[temp_ind]
                    break

            params.offsets_end[ind] = params.chap_ends[ind] - next_uid_start

        params.lengths[ind] = params.ends[ind] - params.starts[ind]

def fill_video_segments():
    params.file_type = 'video'
    params.indexes = []
    params.segments_vid, params.segments_times = [], []
    params.segments_inds = {}

    params.sources, params.lengths = {}, {}

    params.starts, params.ends = params.chap_starts.copy(), params.chap_ends.copy()
    params.offsets_start, params.offsets_end = {}, {}

    params.splitted = params.extracted_orig = False
    params.strict = params.ACCEPT_OFFSETS['video']

    tids = file_info.mkvtools.get_track_type_tids(params.video, 'video')
    params.tid = tids[0]
    params.ind_end = -1

    for params.ind, params.uid in enumerate(params.uids):
        if params.ind <= params.ind_end or params.ind in params.skips or not set_video_source():
            continue
        set_video_segment_info()

    flags.set_splitted.set_flags_by_splitted_params(tids)
