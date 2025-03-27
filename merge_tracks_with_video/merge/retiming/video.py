import os
import sys
from datetime import timedelta

from merge_tracks_with_video.constants import ACCEPT_RETIMING_OFFSETS

class _SegmentSource():
    def _find_source_by_uid(self, uid):
        base_dir = os.path.dirname(self.base_video)
        ftrie = self.merge.files.dir_ftrie_pairs[base_dir]
        idx_start = self.merge.idx_start
        cut_stem = self.merge.stem[:idx_start]
        end_char_slice = idx_start + 1
        sep = os.sep

        for name in ftrie.starts_with(cut_stem):
            if not name[-4:].lower() == '.mkv':
                continue
            # As a rule linked segments not has num in the same place
            elif '0' <= name[idx_start:end_char_slice] <= '9':
                continue

            path = base_dir + sep + name
            _uid = self.merge.files.info.by_query('Segment UID:', path)
            if uid == _uid:
                self.source = path
                return
            else:
                self.uids_info.setdefault(_uid, {})['source'] = path

        # If not found above try all mkv search
        names = ftrie.starts_with('')
        names.sort(reverse=True)
        for name in names:
            if not name[-4:].lower() == '.mkv':
                continue
            if uid == self.merge.files.info.by_query(
                'Segment UID:', base_dir + sep + name
            ):
                self.source = base_dir + sep + name
                return

    def _not_found_source(uid, exit_on_none=False):
        if exit_on_none:
            msg_tail = ('. Please move this file to the video directory and '
                        're-run the script.')
        else:
            msg_tail = ' and has been skipped.'

        print(f"Video file with UID '{uid}' not found in the video directory"
              f"directory '{os.path.dirname(self.base_video)}'.\nThis file "
              f" is a segment of the linked video '{self.base_video}'{msg_tail}")

        if exit_on_none:
            sys.exit(1)
        else:  # Add all uid segments in remove
            remove_uids = self.uids_info.setdefault('remove_uids', set())
            for idx, _uid in enumerate(self.uids):
                if uid == _uid:
                    self.remove_idxs.add(idx)
                    remove_uids.add(uid)

    def set_video_source(self, uid, exit_on_none=False):
        self.uid_info = self.uids_info.setdefault(uid, {})

        if not uid:
            self.source = self.base_video
        else:
            self.source = self.uid_info.get('source', None)
            if self.source is None:
                self._find_source_by_uid(uid)
                if self.source is None:
                    self._not_found_source(uid, exit_on_none)
                else:
                    self.uid_info['source'] = self.source

        return self.source

class Video(_SegmentSource):
    def _set_video_idx_end(self):
        instance_uid = self.uid
        remove_idxs = self.remove_idxs
        for idx, uid in enumerate(self.uids[self.idx:], start=self.idx):
            if uid == instance_uid and idx not in remove_idxs:
                self.idx_end = idx
            elif uid == instance_uid:
                self.is_video_split = True
                break
            elif uid != instance_uid and idx not in remove_idxs:
                if not self.is_video_split:
                    for _uid in self.uids[idx:]:
                        if _uid == instance_uid:
                            self.is_video_split = True
                            break
                break

    def _set_video_split_times(self):
        self._set_video_idx_end()
        self.start = self.end = None
        start = self.chap_starts[self.idx]
        end = self.chap_ends[self.idx_end]
        get_duration = self.merge.files.info.duration
        duration_vid = get_duration(self.source, self.uid, 'video')

        if start + abs(end - duration_vid) < self.strict:
            # Usage full self.source as self.segment
            return True

        elif (not self.uid and
              self.uid_info.get('end', None) and
              abs(start - self.uid_info['end']) < self.strict
        ):
            self.start = self.uid_info['end']
            start = None

        def get_times(_td):
            return self.merge.files.info.i_frames(
                self.source, self.tid, _td, '0.000001')

        for td in [start, end]:
            if td is None:  # If earlier setted
                continue

            times = get_times(td)  # Receive I-frame time <= td
            _delta = td - next(iter(times))
            times.update(get_times(_delta))  # Receive next I-frame
            times.add(duration_vid)  # Also add duration

            # Usage time with lowest offset
            offset = timedelta(seconds=99999)
            for _td in times:
                _offset = abs(td - _td)
                if abs(td - _td) < offset:
                    time = _td
                    offset = abs(td - _td)
            if self.start is None:
                self.start = time
            else:
                self.end = time

        if not self.uid:
            self.uid_info['end'] = self.end

    def _set_video_segment_td(self):
        self.segment = os.path.join(
            self.temp_dir, f'video_segment_{self.idx}_{self.uid}.mkv')
        if self.uid:
            _info = self.uids_info.setdefault(self.segment, {})
        else:
            _info = {}
        uids = self.uids
        remove_idxs = self.remove_idxs

        # Usage full self.source as self.segment
        if self._set_video_split_times():
            self.defacto_start = timedelta(0)
            self.defacto_end = self.merge.files.info.duration(
                self.source, self.uid, 'video')
            self.segment = self.source

        # Usage earlier splitted uid segment
        elif (_info.get('end', None) and
              (abs(_info['start'] - self.start)
               + abs(_info['end'] - self.end)) < self.strict and
              os.path.exists(self.segment)
        ):
            self.defacto_start = _info['start']
            self.defacto_end = _info['end']

        # Usage main segment if not uid segments
        elif all(not uids[idx] or
                 uids[idx] in remove_idxs
                 for idx in range(len(uids))
        ):
            self.defacto_start = self.start
            self.defacto_end = self.end
            self.segment = self.source

        # Split video to get self.segment
        else:
            self.split_file(repeat=False)
            # Save splitted uid segment info for future use
            if self.uid:
                _info['start'] = self.defacto_start
                _info['end'] = self.defacto_end

    def _set_video_segment_info(self):
        self._set_video_segment_td()
        segments = self.video_segments
        segments.setdefault('paths', []).append(self.segment)
        segments.setdefault('times', []).append(
            [self.defacto_start, self.defacto_end])
        segments.setdefault(self.segment, set()).update(
            {self.idx, self.idx_end})

        for idx in range(self.idx, self.idx_end+1):
            if idx in self.remove_idxs:
                continue
            self.indexes.append(idx)
            self.sources[idx] = self.source

            if idx == self.idx:
                self.starts[idx] = self.defacto_start
                self.offsets_start[idx] = (
                    self.defacto_start - self.chap_starts[idx])
            else:
                self.offsets_start[idx] = timedelta(0)

            if idx == self.idx_end:
                self.ends[idx] = self.defacto_end
                self.offsets_end[idx] = (
                    self.defacto_end - self.chap_ends[idx])
            else:
                for _idx, _uid in enumerate(self.uids[idx+1:], start=idx+1):
                    if _uid == self.uid:
                        next_uid_start = self.chap_starts[_idx]
                self.offsets_end[idx] = self.chap_ends[idx] - next_uid_start

            self.lengths[idx] = self.ends[idx] - self.starts[idx]

    def _set_options_by_video_segments(self, tids):
        if self.is_video_split:
            # Usage self.base_video with --split options
            if all(not self.uids[idx] for idx in self.indexes):
                self.video_segments['paths'][:] = [self.base_video]
                def to_timestamp(td):
                    return self.timedelta_to_timestamp(
                        td, decimals_place=6)

                str_times = []
                for times in self.video_segments['times']:
                    start, end = times
                    start = to_timestamp(start)
                    end = to_timestamp(end)
                    str_times.append(f'{start}-{end}')
                str_times = ',+'.join(str_times)
                value = self.get_opt('specials', self.base_video)
                value += ['--split', f'parts:{str_times}']

                self.set_opt('specials', value, self.base_video)
                if len(tids) > 1:
                    self.set_opt('video_tracks', {self.tid}, self.base_video)
            else:
                self.need_extract_orig = True
                if len(tids) > 1:
                    # Splitted segments has only 0 track
                    self.set_opt('video_tracks', {0}, self.base_video)

        if (len(self.video_segments['paths']) > 1 and
            self.get_opt('force_retiming', 'global')
        ):
            self.need_extract_orig = True

        if self.need_extract_orig:
            for group in ['audio', 'subtitles']:
                self.set_opt(f'{group}_tracks', False, self.base_video)

    def update_retimed_video(self):
        first = self.video_segments['paths'][0]
        self.retimed_video[:] = [first]
        self.merge.append_to[first] = self.video_segments['paths'][1:]
        self.merge.replace_targets[first] = (self.base_video, 'video',
                                             self.tid)

    def fill_retimed_video(self):
        # Save first video track. Without re-encoding sync video, audio,
        # and subtitles is possible only for 1 video
        self.video_segments.clear()
        self.retimed_video.clear()
        self.indexes.clear()
        self.ftype = 'video'
        self.strict = ACCEPT_RETIMING_OFFSETS['video']
        self.is_video_split = False
        self.need_extract_orig = False
        tids = self.merge.files.info.tgroup_tids('video', self.base_video)
        self.tid = tids[0]
        self.idx = 0
        self.idx_end = -1
        for self.idx, self.uid in enumerate(self.uids):
            if (self.idx <= self.idx_end or
                self.idx in self.remove_idxs or
                not self.set_video_source(self.uid)
            ):
                continue
            self._set_video_segment_info()

        self._set_options_by_video_segments(tids)
        self.update_retimed_video()
