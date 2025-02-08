from datetime import timedelta

import executor
import splitted.params
from . import by_mkvtools

def get_duration_split_source(key='max'):
    if splitted.params.uid_info.setdefault('duration', {}).get(key, None):
        return splitted.params.uid_info['duration'][key]

    durations = []
    # If audio > video, non-video audio is playback.
    # If subtitles > video, non-video subtitles is not playback.
    for ttype in {'video', 'audio'}:
        # Time in read_intervals will decrease to last I frame
        command = [
            'ffprobe', '-v', 'quiet', '-select_streams', f'{ttype[:1]}',
            '-read_intervals', '99999999999', '-show_entries',
            'frame=pts_time', '-of', 'csv', splitted.params.source
        ]

        for line in reversed(executor.execute(command).splitlines()):
            duration = timedelta(seconds=float(line.split(',')[1]))
            splitted.params.uid_info['duration'][ttype] = duration
            durations.append(duration)
            break

    if not durations:
        duration = by_mkvtools.get_info_by_query('Duration:',
                                                 splitted.params.source)
        splitted.params.uid_info['duration']['video'] = duration
        splitted.params.uid_info['duration']['audio'] = duration
        durations.append(duration)

    splitted.params.uid_info['duration']['max'] = max(durations)

    return splitted.params.uid_info['duration'][key]

def get_times_i_frames_split_source(td, offset_search):
    times = []
    command = [
        'ffprobe', '-v', 'quiet', '-select_streams',
        f'v:{splitted.params.tid}', '-read_intervals',
        f'{td.total_seconds()}%+{offset_search}', '-show_entries',
        'frame=pict_type,pts_time', '-of', 'csv', splitted.params.source
    ]

    for line in executor.execute(command).splitlines():
        if not 'I' in line:
            continue

        times.append(timedelta(seconds=float(line.split(',')[1])))

    return times
