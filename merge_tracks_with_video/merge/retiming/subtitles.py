import os

import srt

from merge_tracks_with_video.constants import ASS_SPECS, EXTS_TUPLE

class _IndepSource():
    def __init__(self, retiming_instance):
        self.retiming = retiming_instance
        self.encoding = self.retiming.merge.files.info.char_encoding

    def _get_ext_tids_pairs(self, fpath, fgroup):
        tids = {}
        ext_key_pairs = {
            '.ass': 'subtitles (SubStationAlpha)',
            '.srt': 'subtitles (SubRip/SRT)',
        }

        tgroup_tids = self.retiming.merge.files.info.tgroup_tids
        total_tids = set(tgroup_tids('subtitles', fpath))
        if not total_tids:
            return tids

        fdir = os.path.dirname(fpath)
        _tracks = self.retiming.get_opt(
            'subtitles_tracks', fpath, fgroup, fdir)
        save_track = self.retiming.save_track

        for ext, key in ext_key_pairs.items():
            _tids = tgroup_tids(key, fpath)
            for tid in _tids:
                if save_track(tid, _tracks):
                    tids.setdefault(ext, []).append(tid)
            total_tids.difference_update(_tids)

        for tid in total_tids:  # remainders
            print(f"Skip subtitles track '{tid}' from the file '{fpath}'."
                  "It track can't be retiming.")

        return tids

    def _extract_track(self, tid, source, out_path):
        command = ['mkvextract', 'tracks', source, f'{tid}:{out_path}']
        msg = f"Extracting subtitles track '{tid}' from the file '{source}'."
        self.execute(command, msg=msg, get_stdout=False)

    def _iterate_section_lines(self, section, source):
        in_section = False
        with open(source, 'r', encoding=self.encoding(source)) as file:
            for line in file:
                if not in_section:
                    if line.startswith('['):
                        if section == line.strip():
                            in_section = True
                else:
                    if line.startswith('['):
                        break  # Begin new section
                    elif line.strip():
                        yield line

    def _write_events_section(self, file):
        section = '[Events]'
        extracted = self.extracted
        timings = self.timings
        sources = self.sources
        indexes = self.retiming.indexes
        to_timedelta = self.retiming.timestamp_to_timedelta
        to_timestamp = lambda td: self.retiming.timedelta_to_timestamp(
                td, hours_place=1, decimals_place=2)
        prefixes = ASS_SPECS['events_prefixes']
        idx_start = ASS_SPECS['events_idx_start']
        idx_end = idx_start + 1
        idx_before_times = idx_end + 1
        written_format = False

        file.write(section + '\n')
        for idx in indexes:
            start, end, offset = timings[idx]
            source = extracted[sources[idx]]
            for line in self._iterate_section_lines(section, source):
                if line.startswith('Format:'):
                    if not written_format:
                        file.write(line)
                        written_format = True

                elif line.startswith(prefixes):
                    parts = line.split(',')
                    _start = to_timedelta(parts[idx_start])
                    _end = to_timedelta(parts[idx_end])

                    if (_start < start and _end < start or
                        _start > end and _end > end
                    ):
                        continue  # Skip non-segment lines

                    else:  # Retime and write
                        new_start = to_timestamp(_start + offset)
                        new_end = to_timestamp(_end + offset)
                        new_line = (','.join(parts[:idx_start])
                                    + f',{new_start},{new_end},'
                                    + ','.join(parts[idx_before_times:])
                                    )
                        file.write(new_line)
        file.write('\n')

    def _write_retimed_srt(self, file):
        extracted = self.extracted
        sources = self.sources
        timings = self.timings
        indexes = self.retiming.indexes

        subs = []
        for idx in indexes:
            start, end, offset = timings[idx]
            source = extracted[sources[idx]]
            with open(source, 'r', encoding=self.encoding(source)) as f:
                for sub in srt.parse(f):
                    _start = sub.start
                    _end = sub.end

                    if (_start < start and _end < start or
                        _start > end and _end > end
                    ):
                        continue  # Skip non-segment lines

                    else:
                        sub.start = _start + offset
                        sub.end = _end + offset
                        subs.append(sub)

        file.write(srt.compose(subs))

class _MultipleSource(_IndepSource):
    def __init__(self, retiming_instance):
        super().__init__(retiming_instance)
        self.timings = {}
        self.extracted = {}
        self.sources = self.retiming.sources
        self._set_timings()

    def _set_timings(self):
        timings = self.timings
        timings.clear()
        indexes = self.retiming.indexes
        get_previous_lengths = self.retiming.get_previous_lengths
        starts = self.retiming.starts
        ends = self.retiming.ends
        offsets_start = self.retiming.offsets_start

        for idx in indexes:
            lengths = get_previous_lengths(idx)
            start = starts[idx]
            end = ends[idx]
            offset = (lengths['nonuid']['defacto']
                      + lengths['uid']['offset']
                      - offsets_start[idx])
            timings[idx] = (start, end, offset)

    def _extract_segments(self, count, tid, ext):
        extracted = self.extracted
        extracted.clear()
        temp_dir = self.retiming.temp_dir
        sources = self.sources
        extract_track = self._extract_track

        idx = 0
        for _, source in sources.items():
            if source in extracted:
                continue
            out_path = os.path.join(
                temp_dir, 'orig_subs',
                f'subs_{count}_segment_{idx}{ext}')
            extract_track(tid, source, out_path)
            extracted[source] = out_path
            idx += 1

    def _write_retimed_ass(self, file):
        extracted = self.extracted
        _key = next(iter(extracted))
        source = extracted[_key]
        written_lines = set()
        section = ''
        iterator = self._iterate_section_lines

        with open(source, 'r', encoding=self.encoding(source)) as f:
            for line in f:
                if not section:
                    if line.startswith('['):
                        line_strip = line.strip()
                        if line_strip == '[Events]':
                            self._write_events_section(file)
                        else:
                            section = line_strip
                else:
                    file.write(section + '\n')
                    for _, _source in extracted.items():
                        for _line in iterator(section, _source):
                            if not _line in written_lines:
                                file.write(_line)
                                written_lines.add(_line)
                    file.write('\n')

                    written_lines.clear()
                    section = ''

    def get_retimed_subtitles(self, count):
        retimed_subtitles = []

        base_video = self.retiming.base_video
        set_replace_targets = self.retiming.set_merge_replace_targets
        ext_tids = self._get_ext_tids_pairs(base_video, 'video')

        for ext, tids in ext_tids.items():
            write_sub = getattr(self, f'_write_retimed_{ext[1:]}')
            for tid in tids:
                self._extract_segments(count, tid, ext)
                retimed = os.path.join(
                    self.retiming.temp_dir, 'orig_subs',
                    f'subs_{count}{ext}')
                with open(retimed, 'w') as file:
                    write_sub(file)

                retimed_subtitles.append(retimed)
                set_replace_targets(retimed, base_video, 'video')
                count += 1

        return retimed_subtitles

class _SingleSource(_IndepSource):
    def __init__(self, retiming_instance):
        super().__init__(retiming_instance)
        self.extracted = {}
        self.sources = {}
        self.timings = {}
        self._set_timings()

    def _set_timings(self):
        timings = self.timings
        timings.clear()
        indexes = self.retiming.indexes
        get_previous_lengths = self.retiming.get_previous_lengths
        starts = self.retiming.starts
        ends = self.retiming.ends
        offsets_start = self.retiming.offsets_start

        for idx in indexes:
            lengths = get_previous_lengths(idx)
            start = starts[idx] + lengths['nonuid']['chapters']
            end = ends[idx] + lengths['nonuid']['chapters']
            offset = (lengths['nonuid']['offset']
                      + lengths['uid']['offset']
                      - offsets_start[idx])
            timings[idx] = (start, end, offset)

    def _write_retimed_ass(self, file):
        _key = next(iter(self.extracted))
        source = self.extracted[_key]
        section = ''

        with open(source, 'r', encoding=self.encoding(source)) as f:
            for line in f:
                if not section:
                    if line.startswith('['):
                        line_strip = line.strip()
                        if line_strip == '[Events]':
                            self._write_events_section(file)
                        else:
                            section = line_strip
                            file.write(line)
                else:
                    file.write(line)
                    if not line.strip():
                        section = ''

    def _get_group_sources_pairs(self):
        pairs = {}
        _base = self.retiming.base_video
        _video = self.retiming.initial_video
        pairs['video'] = [x for x in _video if x != _base]
        pairs['audio'] = self.retiming.initial_audio
        pairs['signs'] = self.retiming.initial_signs
        pairs['subtitles'] = self.retiming.initial_subtitles
        return pairs

    def get_retimed_subtitles(self, count):
        retimed_subtitles = []

        extracted = self.extracted
        sources = self.sources
        get_opt = self.retiming.get_opt
        save_track = self.retiming.save_track
        indexes = self.retiming.indexes
        temp_dir = self.retiming.temp_dir
        set_replace_targets = self.retiming.set_merge_replace_targets

        for group, _sources in self._get_group_sources_pairs().items():
            for source in _sources:
                name_dir = os.path.basename(os.path.dirname(source))
                ext_tids = self._get_ext_tids_pairs(source, group)
                for ext, tids in ext_tids.items():
                    write_sub = getattr(self, f'_write_retimed_{ext[1:]}')
                    for tid in tids:
                        if source.endswith(EXTS_TUPLE['retiming_subtitles']):
                            _extracted = source  # Wo extract
                        else:
                            _extracted = os.path.join(
                                temp_dir, 'ext_subs', name_dir,
                                f'source_subs_{count}{ext}')
                            self._extract_track(tid, source, _extracted)

                        # Double need in _IndepSource methods
                        sources.clear()
                        sources.update({idx: source for idx in indexes})
                        extracted.clear()
                        extracted[source] = _extracted

                        _dir = os.path.join(temp_dir, 'ext_subs', name_dir)
                        os.makedirs(_dir, exist_ok=True)
                        retimed = os.path.join(_dir, f'subs_{count}{ext}')
                        with open(retimed, 'w') as file:
                            write_sub(file)

                        retimed_subtitles.append(retimed)
                        set_replace_targets(retimed, source, group)
                        count += 1

        return retimed_subtitles

class Subtitles():
    def fill_retimed_signs_subtitles(self):
        retimed_signs = self.retimed_signs
        retimed_subtitles = self.retimed_subtitles
        retimed_signs.clear()
        retimed_subtitles.clear()
        retimed_list = []

        if self.need_extract_orig:
            count = 0
            multiple_source = _MultipleSource(self)
            retimed_list += multiple_source.get_retimed_subtitles(count)

        count = len(retimed_list)
        single_source = _SingleSource(self)
        retimed_list += single_source.get_retimed_subtitles(count)

        # Let's sort retimed
        is_signs = self.merge.files.info.is_signs
        replace_targets = self.merge.replace_targets
        acceptable_groups = {'signs', 'subtitles'}
        for path in retimed_list:
            _path, group, tid = replace_targets[path]
            if group not in acceptable_groups:
                group = 'signs' if is_signs(_path, [tid]) else 'subtitles'

            if group == 'signs':
                retimed_signs.append(path)
            else:
                retimed_subtitles.append(path)
