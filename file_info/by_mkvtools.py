import os
import re

import executor
import type_convert
from . import setted
from files.constants import MATROSKA_DEFAULT, SUFFIXES

def get_mkvmerge_i_stdout(fpath):
    stdouts = setted.info.setdefault(fpath, {}).setdefault('stdouts', {})

    if stdouts.get('mkvmerge_i', None) is not None:
        return stdouts['mkvmerge_i']

    else:
        stdout = executor.execute(['mkvmerge', '-i', fpath])
        stdouts['mkvmerge_i'] = stdout
        return stdout

def file_has_video_track(fpath):
    return True if 'video' in get_mkvmerge_i_stdout(fpath) else False

def get_file_group(fpath):
    if setted.info.setdefault(fpath, {}).get('file_group', None):
        return setted.info[fpath]['file_group']

    if fpath.endswith(SUFFIXES['subtitles']):
        fgroup = 'subtitles'
    elif file_has_video_track(fpath):
        fgroup = 'video'
    else:
        fgroup = 'audio'

    setted.info[fpath]['file_group'] = fgroup
    return fgroup

def get_track_type_tids(track_type, fpath):
    info = setted.info.setdefault(fpath, {}).setdefault('track_type_tids', {})

    if info.get(track_type, None) is not None:
        return info[track_type]

    if fpath.endswith(SUFFIXES['single_track']):
        tids = [0] if fpath.endswith(SUFFIXES[track_type]) else []
        info[track_type] = tids
        return tids

    tids = []
    pattern = r"Track ID (\d+):"

    for line in get_mkvmerge_i_stdout(fpath).splitlines():
        if track_type in line:
            match = re.search(pattern, line)
            if match:
                tids.append(int(match.group(1)))

    info[track_type] = tids
    return tids

def get_mkvinfo_stdout(fpath):
    stdouts = setted.info.setdefault(fpath, {}).setdefault('stdouts', {})

    if stdouts.get('mkvinfo', None) is not None:
        return stdouts['mkvinfo']

    else:
        stdout = executor.execute(['mkvinfo', fpath])
        stdouts['mkvinfo'] = stdout
        return stdout

def filter_stdout_mkvinfo_by_tid(stdout_lines, tid):
    ind = ind_end = 0
    start_pattern = rf"\s*Track number:\s*{tid}"
    end_pattern = rf"\s*Track number:\s*{tid+1}"

    for ind, line in enumerate(stdout_lines):
        if re.search(start_pattern, line):
            break

    for ind_end, line in enumerate(stdout_lines[ind:], start=ind):
        if re.search(end_pattern, line):
            break

    return stdout_lines[ind:ind_end]

def get_info_by_query(query, fpath, tid=None):
    if not fpath.endswith(SUFFIXES['mkvtools_supported']):
        return ''

    stdout_lines = get_mkvinfo_stdout(fpath).splitlines()
    if tid is not None:
        # Mkvinfo uses 1-based indexing (add 1 to tid for mkvmerge)
        stdout_lines = filter_stdout_mkvinfo_by_tid(stdout_lines, tid+1)

    for line in stdout_lines:
        if query in line:
            value = line.split(':', 1)[1].strip()

            if 'Segment UID:' in query:
                return ''.join(
                    byte[2:] if byte.startswith('0x') else byte
                    for byte in value.split()
                )

            elif 'Duration:' in query:
                return type_convert.str_to_timedelta(value)

            else:
                return value if value != 'und' else ''

    return MATROSKA_DEFAULT.get(query.lower(), '')
