import re
from datetime import timedelta

from merge_tracks_with_video.constants import (
    ACCEPT_RETIMING_OFFSETS,
    ACCURACY_TIMEDELTA,
    SECONDS_IN_HOUR,
    SECONDS_IN_MINUTE,
    TIMESTAMP_MKVTOOLNIX
)

class TimestampCast():
    @classmethod
    def timestamp_to_timedelta(cls, timestamp):
        hours, minutes, seconds = timestamp.split(':')
        total_seconds = int(hours) * SECONDS_IN_HOUR
        total_seconds += int(minutes) * SECONDS_IN_MINUTE
        total_seconds += float(seconds)
        return timedelta(seconds=total_seconds)

    @classmethod
    def timedelta_to_timestamp(cls, td, **kwargs):
        std = TIMESTAMP_MKVTOOLNIX
        hours_place = kwargs.get('hours_place', std['hours_place'])
        minutes_place = kwargs.get('minutes_place', std['minutes_place'])
        seconds_place = kwargs.get('seconds_place', std['seconds_place'])
        decimals_place = kwargs.get('decimals_place', std['decimals_place'])

        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, SECONDS_IN_HOUR)
        minutes, seconds = divmod(remainder, SECONDS_IN_MINUTE)
        d, dp = td.microseconds, decimals_place
        if dp <= ACCURACY_TIMEDELTA:
            decimals = int(d / (10 ** (ACCURACY_TIMEDELTA - dp)))
        else:
            decimals = d * 10 ** (dp - ACCURACY_TIMEDELTA)

        return (
            f'{hours:0{hours_place}}:{minutes:0{minutes_place}}:'
            f'{seconds:0{seconds_place}}.{decimals:0{decimals_place}}')

class _SplitFile():
    def _get_split_command(self):
        command = [
            'mkvmerge', '-o', self.segment, '--split',
            f'parts:{self.start}-{self.end}', '--no-chapters',
            '--no-global-tags', '--no-subtitles', '--no-attachments',
            f'--{self.ftype}-tracks', f'{self.tid}'
        ]
        if self.ftype == 'video':
            command.append('--no-audio')
        else:
            command.append('--no-video')
        command.append(self.source)
        return command

    def _set_splitted_segment_info(self, mkvmerge_stdout):
        duration = None
        pattern = (r'Timestamp used in split decision: '
                   + TIMESTAMP_MKVTOOLNIX['pattern'])
        timestamps = re.findall(pattern, mkvmerge_stdout)
        timestamps = [x.split(':', 1)[1] for x in timestamps]
        to_timedelta = self.timestamp_to_timedelta

        if len(timestamps) == 2:
            defacto_start = to_timedelta(timestamps[0])
            defacto_end = to_timedelta(timestamps[1])
        elif len(timestamps) == 1:
            timestamp = to_timedelta(timestamps[0])
            if self.start > timedelta(0):  # Timestamp for start
                defacto_start = timestamp
                duration = self.merge.files.info.by_query(
                    'Duration:', self.segment)
                defacto_end = defacto_start + duration
            else:
                defacto_start = timedelta(0)
                defacto_end = timestamp
        else:
            defacto_start = timedelta(0)
            duration = self.merge.files.info.by_query(
                'Duration:', self.segment)
            defacto_end = duration

        # Defacto playback <= track duration
        if duration and defacto_end <= self.end:
            self.offset_end = timedelta(0)
        else:
            self.offset_end = defacto_end - self.end
        self.offset_start = defacto_start - self.start
        self.length = defacto_end - defacto_start
        self.defacto_start = defacto_start
        self.defacto_end = defacto_end

    def split_file(self, repeat=True):
        command = self._get_split_command()
        msg = (f"Extracting a segment of the '{self.ftype}' track from "
               f"the file '{self.source}'.")
        self._set_splitted_segment_info(self.execute(command, msg=msg))

        # Mkvmerge shift split times to next I-frame. Try repeat split
        # with new timestamps by offsets
        if (repeat and
            any(td > ACCEPT_RETIMING_OFFSETS[self.ftype]
                for td in [self.offset_start, self.offset_end])
        ):
            old_start = self.start
            old_end = self.defacto_end - self.offset_end
            _start = self.start - self.offset_start
            if _start > timedelta(0):
                self.start = _start
            self.end = self.end - self.offset_end

            self.split_file(repeat=False)
            self.offset_start = self.defacto_start - old_start
            self.offset_end = self.defacto_end - old_end

class Common(_SplitFile, TimestampCast):
    def add_remove_idxs(self):
        def get_remove_names():
            names = set()
            remove_segments = self.get_opt('remove_segments')
            names.update({name.lower() for name in remove_segments})
            return names

        names = get_remove_names()
        linked_segments = self.get_opt('linked_segments')
        remove_uids = self.uids_info.get('remove_uids', set())

        for idx, name in enumerate(self.names):
            uid = self.uids[idx]
            if (name.lower() in names or
                not linked_segments and uid or
                uid in remove_uids
            ):
                self.remove_idxs.add(idx)

    def get_previous_lengths(self, idx):
        lengths = {}
        for x in ['uid', 'nonuid']:
            for _x in ['chapters', 'defacto']:  # Init
                lengths.setdefault(x, {})[_x] = timedelta(0)

        for _idx in range(idx):
            x = 'uid' if self.uids[_idx] == self.uids[idx] else 'nonuid'
            lengths[x]['chapters'] += (
                self.chap_ends[_idx] - self.chap_starts[_idx])
            if _idx in self.indexes:
                lengths[x]['defacto'] += self.ends[_idx] - self.starts[_idx]

        for x in ['uid', 'nonuid']:
            lengths[x]['offset'] = (
                lengths[x]['defacto'] - lengths[x]['chapters'])

        return lengths
