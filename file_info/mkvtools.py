import re
from pathlib import Path

import executor
import type_convert
from .keys import EXTENSIONS, KEYS

def file_has_video_track(filepath):
    command = ['mkvmerge', '-i', str(filepath)]
    return True if 'video' in executor.execute(command) else False

def get_track_type_tids(filepath, track_type):
    tids = []

    if filepath.suffix in EXTENSIONS['single_track']:
        return [0] if filepath.suffix in EXTENSIONS[track_type] else []

    track_type = track_type if track_type != "subs" else "subtitles"
    pattern = r"Track ID (\d+):"

    for line in executor.execute(['mkvmerge', '-i', str(filepath)]).splitlines():
        if track_type in line:
            match = re.search(pattern, line)
            if match:
                tids.append(int(match.group(1)))
    return tids

def cut_stdout_for_track(stdout_lines, tid):
    start_pattern = rf"\s*Track number:\s*{tid}"
    end_pattern = rf"\s*Track number:\s*{tid+1}"

    for ind, line in enumerate(stdout_lines):
        if re.search(start_pattern, line):
            break

    for ind_end, line in enumerate(stdout_lines[ind:], start=ind):
        if re.search(end_pattern, line):
            break

    return stdout_lines[ind:ind_end]

def get_file_info(filepath, query, tid=None):
    if filepath.suffix not in EXTENSIONS['mkvtools_supported']:
        return ''

    stdout_lines = executor.execute(['mkvinfo', str(filepath)]).splitlines()
    if tid is not None:
        stdout_lines = cut_stdout_for_track(stdout_lines, tid+1)
                                     #tid mkvinfo +1 to mkvmerge

    for line in stdout_lines:
        if query in line:
            value = line.split(':', 1)[1].strip()

            if "Segment UID:" in query:
                return ''.join(
                    byte[2:] if byte.startswith('0x') else byte
                    for byte in value.split()
                )

            elif "Duration:" in query:
                return type_convert.str_to_timedelta(value)

            else:
                return value if value != 'und' else ''

    return KEYS['default_matroska'].get(query.lower(), '')
