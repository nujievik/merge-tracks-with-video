import os
from datetime import timedelta

class Audio():
    def _get_audio_to_retime(self):
        to_retime = []
        base_video = self.base_video
        tgroup_tids = self.merge.files.info.tgroup_tids

        if self.audio_tracks and self.need_extract_orig:
            _tracks = self.audio_tracks
            for tid in tgroup_tids('audio', base_video):
                if self.save_track(tid, _tracks):
                    to_retime.append((base_video, 'video', tid))

        sources = [vid for vid in self.initial_video if vid != base_video]
        len_vid = len(sources)
        sources.extend(self.initial_audio)
        for idx, source in enumerate(sources):
            fgroup = 'video' if idx < len_vid else 'audio'
            parent_dir = os.path.dirname(source)
            _tracks = self.get_opt('audio_tracks', source, fgroup, parent_dir)
            for tid in tgroup_tids('audio', source):
                if self.save_track(tid, _tracks):
                    to_retime.append((source, fgroup, tid))

        return to_retime

    def _get_segments_multiple_src_audio(self, count):
        segments = []
        lengths = {}

        for idx in self.indexes:
            self.start = self.starts[idx]
            self.end = self.ends[idx]
            offset = (lengths.setdefault('audio', timedelta(0))
                      - lengths.setdefault('video', timedelta(0)))
            if self.start + offset >= timedelta(0):
                self.start = self.start + offset

            self.segment = os.path.join(
                self.temp_dir, 'orig_audio',
                f'audio_{count}_segment_{idx}.mka')
            self.source = self.sources[idx]
            self.split_file()
            segments.append(self.segment)

            lengths['video'] += self.lengths[idx]
            lengths['audio'] += self.length

        return segments

    def _get_segments_single_src_audio(self, count):
        segments = []
        lengths = {}

        for idx in self.indexes:
            nonuid_length = self.get_previous_lengths(idx)['nonuid']['chapters']
            offset = (lengths.setdefault('audio', timedelta(0))
                      - lengths.setdefault('video', timedelta(0)))
            _start = self.starts[idx] + nonuid_length + offset
            if _start >= timedelta(0):
                self.start = _start
            else:
                self.start -= offset
            self.end = self.ends[idx] + nonuid_length

            self.segment = os.path.join(
                self.temp_dir, 'ext_audio',
                os.path.basename(os.path.dirname(self.source)),
                f'audio_{count}_segment_{idx}.mka')
            self.split_file()
            segments.append(self.segment)

            lengths['video'] += self.lengths[idx]
            lengths['audio'] += self.length

        return segments

    def fill_retimed_audio(self):
        self.retimed_audio.clear()
        self.ftype = 'audio'

        _to_retime = self._get_audio_to_retime()
        for count, tmp in enumerate(_to_retime):
            self.source = tmp[0]
            fpath, fgroup, self.tid = tmp

            if self.source == self.base_video:
                segments = self._get_segments_multiple_src_audio(count)
            else:
                segments = self._get_segments_single_src_audio(count)

            first = segments[0]
            self.retimed_audio.append(first)
            self.merge.append_to[first] = segments[1:]
            self.set_merge_replace_targets(first, fpath, fgroup)
