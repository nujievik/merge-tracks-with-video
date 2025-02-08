import os
from datetime import timedelta

import executor
import files.found
import options.set_methods
import file_info.by_ffprobe
import file_info.by_mkvtools
from . import common, params

def get_base_dir_fpaths():
    if params.base_dir_fpaths:
        return params.base_dir_fpaths

    if len(files.found.stems_dict) != len(files.found.prefixes):
        files.found.prefixes = tuple(files.found.stems_dict.keys())

    params.base_dir = os.path.dirname(params.base_video) + os.sep
    fnames = os.listdir(params.base_dir)
    filtered_by_prefixes = [
        f for f in fnames if not f.startswith(files.found.prefixes)
    ]
    params.base_dir_fpaths = [
        f'{params.base_dir}{f}' for f in filtered_by_prefixes + fnames]

    return params.base_dir_fpaths

def find_source_by_uid():
    for f in get_base_dir_fpaths():
        if (f.endswith('.mkv') and
            params.uid == file_info.by_mkvtools.get_info_by_query(
                'Segment UID:', f)
            ):
            params.source = params.uid_info['source'] = f
            break

def not_found_source(exit_if_none=False):
    if exit_if_none:
        msg_tail = ('. Please move this file to the video directory and '
                    're-run the script.')
    else:
        msg_tail = ' and has been skipped.'

    print(f"Video file with UID '{params.uid}' not found in the video "
          f"directory '{os.path.dirname(params.base_video)}'.\nThis file is "
          f"a segment of the linked video '{params.base_video}'{msg_tail}")

    if exit_if_none:
        executor.remove_temp_files()

    else:  # Add all uid segments in skips
        for ind, uid in enumerate(params.uids[params.ind:], start=params.ind):
            if uid == params.uid:
                params.skips.add(ind)
            params.segments.setdefault('skips_uid', set()).add(params.uid)

def set_video_source(exit_if_none=False):
    params.uid_info = params.segments.setdefault(params.uid, {})

    if not params.uid:
        params.source = params.base_video
        return params.source

    params.source = params.uid_info.get('source', None)
    if not params.source:
        find_source_by_uid()

    if params.source:
        return params.source
    else:
        not_found_source(exit_if_none)

def set_video_ind_end():
    for ind, uid in enumerate(params.uids[params.ind:], start=params.ind):

        if uid == params.uid and ind not in params.skips:
            params.ind_end = ind

        elif uid == params.uid:
            params.is_splitted = True
            break

        elif uid != params.uid and ind not in params.skips:
            if not params.is_splitted:
                for uid in params.uids[ind:]:
                    if uid == params.uid:
                        params.is_splitted = True
                        break
            break

def set_video_split_times():
    set_video_ind_end()

    params.start = params.end = None
    start = params.chap_starts[params.ind]
    end = params.chap_ends[params.ind_end]

    duration_vid = file_info.by_ffprobe.get_duration_split_source('video')

    if start + abs(end - duration_vid) < params.strict:
        return True

    elif (not params.uid and
          params.uid_info.get('end', None) and
          abs(start - params.uid_info['end']) < params.strict
          ):
        params.start = params.uid_info['end']

    for ind, td in enumerate([start, end]):
        if not ind and params.start is not None:
            continue

        times_method = file_info.by_ffprobe.get_times_i_frames_split_source
        times = times_method(td, '0.000001')
        times.append(params.uid_info['duration']['video'])
        times.extend(times_method(td, 2*(td - times[0])))

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
    params.segment = os.path.join(
        params.temp_dir, f'video_segment_{params.ind}_{params.uid}.mkv')

    if params.uid:
        info = params.segments.setdefault(params.segment, {})
    else:
        info = {}

    if set_video_split_times():
        params.defacto_start = timedelta(0)
        duration = file_info.by_ffprobe.get_duration_split_source('video')
        params.defacto_end = duration
        params.segment = params.source

    elif (info.get('end', None) and
          (abs(info['start'] - params.start)
           + abs(info['end'] - params.end)) < params.strict
          ):
        params.defacto_start = info['start']
        params.defacto_end = info['end']

    elif all(not params.uids[ind] or
             params.uids[ind] in params.skips
             for ind in range(0, len(params.uids))
             ):
        params.defacto_start = params.start
        params.defacto_end = params.end
        params.segment = params.source

    else:
        common.split_file(repeat=False)
        if params.uid:
            info['start'] = params.defacto_start
            info['end'] = params.defacto_end

def set_video_segment_info():
    set_video_segment_td()

    params.segments_vid.append(params.segment)
    params.segments_times.append([params.defacto_start, params.defacto_end])
    params.segments_inds.setdefault(params.segment, set()).update(
        {params.ind, params.ind_end})

    for ind in range(params.ind, params.ind_end + 1):
        if ind in params.skips:
            continue

        params.indexes.append(ind)
        params.sources[ind] = params.source

        if ind == params.ind:
            params.starts[ind] = params.defacto_start
            params.offsets_start[ind] = (params.defacto_start
                                         - params.chap_starts[ind])
        else:
            params.offsets_start[ind] = timedelta(0)

        if ind == params.ind_end:
            params.ends[ind] = params.defacto_end
            params.offsets_end[ind] = (params.defacto_end
                                       - params.chap_ends[ind])
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

    params.starts = params.chap_starts.copy()
    params.ends = params.chap_ends.copy()
    params.offsets_start, params.offsets_end = {}, {}

    params.is_splitted = params.extracted_orig = False
    params.strict = params.ACCEPT_OFFSETS['video']

    tids = file_info.by_mkvtools.get_track_type_tids(
        'video', params.base_video)
    params.tid = tids[0]
    params.ind_end = -1

    for params.ind, params.uid in enumerate(params.uids):
        if (params.ind <= params.ind_end or
            params.ind in params.skips or
            not set_video_source()
            ):
            continue
        set_video_segment_info()

    options.set_methods.set_options_by_splitted_params(tids)
