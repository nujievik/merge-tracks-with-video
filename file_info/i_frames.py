from datetime import timedelta

import executor
from splitted import params

def get_times_i_frames(td, offset_search):
    times = []
    command = [
        'ffprobe', '-v', 'quiet', '-select_streams', f'v:{params.tid}', '-read_intervals',
        f'{td.total_seconds()}%+{str(offset_search)}', '-show_entries', 'frame=pict_type,pts_time',
        '-of', 'csv', str(params.source)
    ]

    for line in executor.execute(command).splitlines():
        if not 'I' in line:
            continue

        times.append(timedelta(seconds=float(line.split(',')[1])))

    return times
