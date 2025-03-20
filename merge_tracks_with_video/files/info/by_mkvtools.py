import re
from datetime import timedelta

from constants import (
    EXTS_TUPLE,
    MATROSKA_DEFAULT,
    PATTERNS,
    SECONDS_IN_HOUR,
    SECONDS_IN_MINUTE
)
import tools

class _Stdouts():
    def stdout_mkvmerge_i(self, fpath):
        _info = self.setted.setdefault(fpath, {}).setdefault('stdouts', {})

        if _info.get('mkvmerge_i', None) is not None:
            return _info['mkvmerge_i']

        else:
            stdout = tools.execute(['mkvmerge', '-i', fpath])
            stdout = stdout.splitlines()
            _info['mkvmerge_i'] = stdout
            return stdout

    def _cut_stdout_mkvinfo(self, stdout, tid):
        # Mkvinfo uses 1-based indexing (add 1 to tid for mkvmerge)
        tid += 1
        idx = idx_end = 0
        start_pattern = rf'\s*Track number:\s*{tid}'
        end_pattern = rf'\s*Track number:\s*{tid+1}'

        for idx, line in enumerate(stdout):
            if re.search(start_pattern, line):
                break
        for idx_end, line in enumerate(stdout[idx:], start=idx):
            if re.search(end_pattern, line):
                break

        return stdout[idx:idx_end]

    def _stdout_mkvinfo(self, fpath, tid=None):
        _info = self.setted.setdefault(fpath, {}).setdefault('stdouts', {})

        if _info.get('mvkinfo', None) is not None:
            stdout = _info['mkvinfo']
        else:
            stdout = tools.execute(['mkvinfo', fpath])
            stdout = stdout.splitlines()
            _info['mkvinfo'] = stdout

        if tid is None:
            return stdout
        else:
            return self._cut_stdout_mkvinfo(stdout, tid)

class ByMkvtools(_Stdouts):
    def _timestamp_to_timedelta(self, timestamp):
        hours, minutes, seconds = timestamp.split(':')
        total_seconds = int(hours) * SECONDS_IN_HOUR
        total_seconds += int(minutes) * SECONDS_IN_MINUTE
        total_seconds += float(seconds)
        return timedelta(seconds=total_seconds)

    def by_query(self, query, fpath, tid=None):
        if not fpath.endswith(EXTS_TUPLE['matroska']):
            return ''

        for line in self._stdout_mkvinfo(fpath, tid):
            if query in line:
                value = line.split(':', 1)[1].strip()
                if 'Segment UID:' in query:
                    return ''.join(
                        byte[2:] if byte.startswith('0x') else byte
                        for byte in value.split()
                    )
                elif 'Duration:' in query:
                    return self._timestamp_to_timedelta(value)
                else:
                    return value if value != 'und' else ''

        _key = query.lower().split(':', 1)[0]
        return MATROSKA_DEFAULT.get(_key, '')

    def file_tids(self, fpath):
        _info = self.setted.setdefault(fpath, {})

        if _info.get('tids', None) is not None:
            return _info['tids']

        tids = []
        pattern = r"Track ID (\d+):"

        for line in self.stdout_mkvmerge_i(fpath):
            match = re.search(pattern, line)
            if match:
                tids.append(int(match.group(1)))

        _info['tids'] = tids
        return tids

    def tgroup_tids(self, tgroup, fpath):
        _info = self.setted.setdefault(
            fpath, {}).setdefault('tgroup_tids', {})

        if _info.get(tgroup, None) is not None:
            return _info[tgroup]

        tids = []
        pattern = r"Track ID (\d+):"

        for line in self.stdout_mkvmerge_i(fpath):
            if tgroup in line:
                match = re.search(pattern, line)
                if match:
                    tids.append(int(match.group(1)))

        _info[tgroup] = tids
        return tids

    def is_signs(self, fpath, tids=[]):
        keys = PATTERNS['signs']

        if self.path_has_key(fpath, keys):
            return True

        if not tids:
            tids = self.tgroup_tids('subtitles', fpath)
        for tid in tids:
            tname = self.track_name(tid, fpath, 'subtitles')
            if self.path_has_key(tname, keys):
                return True

        return False

    def file_group(self, fpath):
        _info = self.setted.setdefault(fpath, {})

        if _info.get('file_group', None) is not None:
            return _info['file_group']

        stdout = self.stdout_mkvmerge_i(fpath)
        str_stdout = '\n'.join(stdout)
        for fg in ('video', 'audio', 'subtitles'):
            if fg in str_stdout:
                fgroup = fg
                break

        if fgroup == 'subtitles' and self.is_signs(fpath):
            fgroup = 'signs'

        _info['file_group'] = fgroup
        return fgroup
