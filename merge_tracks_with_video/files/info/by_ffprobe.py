from datetime import timedelta

class ByFfprobe():
    def duration(self, fpath, uid, key='max'):
        _info = self.setted_info.setdefault('uid', {}).setdefault(
            uid, {}).setdefault('duration', {})

        if _info.get(key, None) is not None:
            return _info[key]

        durations = []
        # If audio > video, non-video audio is playback.
        # If subtitles > video, non-video subtitles is not playback.
        for tgroup in ['video', 'audio']:
            # Time in read_intervals will decrease to last I frame
            command = [
                'ffprobe', '-select_streams', f'{tgroup[:1]}',
                '-read_intervals', '99999999999', '-show_entries',
                'frame=pts_time', '-of', 'csv', fpath
            ]
            stdout = self.tools.execute(command)
            for line in reversed(stdout.splitlines()):
                duration = timedelta(seconds=float(line.split(',')[1]))
                if duration:
                    _info[tgroup] = duration
                    durations.append(duration)
                    break

        # Some builds of ffprobe incorrectly process the large
        # -read_intervals option. In this case, use the value from
        # mkvinfo
        if not durations:
            duration = self.by_query('Duration:', fpath)
            _info['video'] = duration
            _info['audio'] = duration
            durations.append(duration)

        _info['max'] = max(durations)
        return _info[key]

    def i_frames(self, fpath, tid, td, offset_search):
        times = set()
        command = [
            'ffprobe', '-select_streams', f'v:{tid}', '-read_intervals',
            f'{td.total_seconds()}%+{offset_search}', '-show_entries',
            'frame=pict_type,pts_time', '-of', 'csv', fpath
        ]
        stdout = self.tools.execute(command)
        for line in stdout.splitlines():
            if 'I' in line:
                times.add(timedelta(seconds=float(line.split(',')[1])))
        return times
