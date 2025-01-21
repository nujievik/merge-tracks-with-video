from datetime import timedelta

import executor
from . import mkvtools
from splitted import params

def get_duration(key='max'):
    if params.uid_info.setdefault('duration', {}).get(key, None):
        return params.uid_info['duration'][key]

    durations = []

    for ttype in ['video', 'audio']: #If audio > video, non-video audio is playback. If subs > video, non-video subs is not playback
        command = [
            'ffprobe', '-v', 'quiet', '-select_streams', f'{ttype[:1]}', '-read_intervals',
            '99999999999', '-show_entries', 'frame=pts_time', '-of', 'csv', str(params.source)
        ] #time will decrease to last I frame

        for line in reversed(executor.execute(command).splitlines()):
            duration = params.uid_info['duration'][ttype] = timedelta(seconds=float(line.split(',')[1]))
            durations.append(duration)
            break

    if not durations:
        duration = mkvtools.get_file_info(params.source, 'Duration:')

        params.uid_info['duration']['video'] = params.uid_info['duration']['audio'] = duration
        durations.append(duration)

    params.uid_info['duration']['max'] = max(durations)

    return params.uid_info['duration'][key]
