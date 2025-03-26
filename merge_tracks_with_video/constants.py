import itertools
import os
from datetime import timedelta

TOOLS = {
    'names': {
        'ffprobe',
        'mkvextract',
        'mkvinfo',
        'mkvmerge',
    },

    'packages': {
        'ffmpeg': {
            'ffprobe',
        },

        'mkvtoolnix': {
            'mkvextract',
            'mkvinfo',
            'mkvmerge',
        },
    },

    'quiet': ('ffprobe', 'ffprobe.exe'),
}


#
# Options constants
#

DEFAULT_OPTS = {
    'global': {
        'start_directory': os.getcwd(),
        'save_directory': os.getcwd(),

        'output': None,  # By default usage orig name + suffixes
        'continue_on_error': False,

        'verbose': None,
        'pro_mode': False,
        'locale_language': 'rus',
        'range_generate': [0, 9999999],

        'limit_generate': 9999999,
        'limit_search_above': 3,
        'limit_check_files': 128,
        #'limit_tracks': 9999999,

        'adding_default_track_flags': True,
        'adding_forced_display_flags': True,
        'adding_languages': True,
        'adding_sub_charsets': True,
        'adding_track_enabled_flags': True,
        'adding_track_names': True,
        'adding_track_orders': True,

        'remove_segments': set(),
        'linked_segments': True,
        'force_retiming': True,

        'audio_tracks': True,
        'video_tracks': True,
        'subtitles_tracks': True,
        'fonts': True,
        'sorting_fonts': True,
        'chapters': True,

        'track_name': '',
        'language': '',
        # By default None-value flags is restricted to limits
        'forced_display_flag': None,
        'limit_forced_display_flag': 0,
        'default_track_flag': None,
        'limit_default_track_flag': 1,
        'track_enabled_flag': None,
        'limit_track_enabled_flag': 9999999,

        'specials': [],
        'target': 'global',
        'files': True,

        'skip_file_patterns': {
            '_added_',
            '_cutted_',
            '_merged_',
            '_replaced_',
        },

        'skip_directory_patterns': {
            '__temp_files__'
            'bdmenu',
            'bonus',
            'commentary',
            'creditless',
            'endings',
            'extra',
            'nc',
            'nd',
            'op',
            'openings',
            'pv',
            'special',
            'specials',
            'бонус',
        },
    },
}

INVERSE_UNSET_ON_PRO = {
    x for x in DEFAULT_OPTS['global'] if x.startswith('adding')
}
INVERSE_UNSET_ON_PRO.add('sorting_fonts')

PATTERNS = {
    'bool': {
        'true': True,
        'on': True,
        '1': True,
        'false': False,
        'off': False,
        '0': False,
    },

    'languages': {
        'rus': {
            'ru',
            'rus',
            'russian',
            'надписи',
            'субтитры',
        },

        'eng': {
            'en',
            'eng',
            'english',
        },

        'jpn': {
            'ja',
            'japanese',
            'jp',
            'jpn',
        },
    },

    'signs': {
        'signs',
        'надписи',
    },
}

SETTING_OPTS = {
    'action_append': {
        'default_track_flag',
        'forced_display_flag',
        'language',
        'track_enabled_flag',
        'track_name',
    },

    'auxiliary': {
        'pos_save_directory',
        'pos_start_directory',
        'target',
    },

    'config': {
        'bool_maybe': {
            'audio_tracks',
            'subtitle_tracks',
            'video_tracks',
        },

        'bool_only': {
            'continue_on_error',
            'fonts',
            'force_retiming',
            'linked_segments',
            'pro_mode',
            'search_above',
            'sorting_fonts',
            'verbose',
        },

        'bool_replace_keys': {
            'subtitle_tracks': 'subtitles_tracks',
        },

        'split': {
            'target',
        },
    },

    'special_targets': {
        'audio',
        'global',
        'signs',
        'subtitles',
        'video',
    }
}
SETTING_OPTS['config']['split'].update(
    {x for x in TOOLS['names']})


#
# Files constants
#

CHUNK_SIZE_READ = 1024 * 1024  # 1 MiB

EXTS = {
    # Common for video and audio
    'container': {
        '.3gp',
        '.av1',
        '.avi',
        '.f4v',
        '.flv',
        '.m2ts',
        '.mkv',
        '.mp4',
        '.mpg',
        '.mov',
        '.mpeg',
        '.ogg',
        '.ogm',
        '.ogv',
        '.ts',
        '.webm',
        '.wmv'
    },

    'video': {
        '.264',
        '.265',
        '.avc',
        '.h264',
        '.h265',
        '.hevc',
        '.ivf',
        '.m2v',
        '.mpv',
        '.obu',
        '.vc1',
        '.x264',
        '.x265',
        '.m4v'
    },

    'audio': {
        '.aac',
        '.ac3',
        '.caf',
        '.dts',
        '.dtshd',
        '.eac3',
        '.ec3',
        '.flac',
        '.m4a',
        '.mka',
        '.mlp',
        '.mp2',
        '.mp3',
        '.mpa',
        '.opus',
        '.ra',
        '.thd',
        '.truehd',
        '.tta',
        '.wav',
        '.weba',
        '.webma',
        '.wma'
    },

    'subtitles': {
        '.ass',
        '.mks',
        '.srt',
        '.ssa',
        '.sub',
        '.sup'
    },

    'fonts': {
        '.otf',
        '.ttf'
    },

    'matroska': {
        '.mka',
        '.mks',
        '.mkv',
        # WebM global metadata is based on the Matroska tag specs.
        # Also mkvinfo is support .webm
        '.webm'
    },

    'retiming_subtitles': {
        '.ass',
        '.srt'
    },
}
EXTS['video'].update(EXTS['container'])
EXTS['audio'].update(EXTS['container'])
EXTS['with_tracks'] = EXTS['video'].union(
    EXTS['audio'], EXTS['subtitles'])
EXTS['total'] = EXTS['with_tracks'].union(EXTS['fonts'])

EXTS_LOWER = {x: exts.copy() for x, exts in EXTS.items()}

def _get_optimal_lengths(group):
    optimal = []
    exts = EXTS_LOWER[group]
    lengths = (len(ext) for ext in exts)
    length_count = {}
    for length in lengths:
        cnt = length_count.get(length, 0)
        length_count[length] = cnt + 1

    total = len(exts)
    chance_length = {
        count / total: length
        for length, count in length_count.items()
    }
    for chance in sorted(chance_length, reverse=True):
        optimal.append(chance_length[chance])

    return optimal

EXTS_LENGTHS = {x: _get_optimal_lengths(x) for x in EXTS_LOWER}

# Add all possible combinations of chars
for group, exts in EXTS.items():
    to_upd = set()
    for ext in exts:
        to_upd.update({
            ''.join(comb)
            for comb in itertools.product(
                *[(char.lower(), char.upper())
                  for char in ext]
            )
        })
    exts.update(to_upd)
# Clear namespace
del group, exts, ext, to_upd

# The Matroska(tm) specification states that some elements have a
# default value. Source: (https://mkvtoolnix.download/doc/mkvmerge.html
# #mkvmerge.default_values)
MATROSKA_DEFAULT = {
    'language': 'eng',
}


#
# Retiming constants
#

ACCURACY_TIMEDELTA = 6
SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60

ASS_SPECS = {
    'events_idx_start': 1,

    'events_prefixes': (
        'Comment:',
        'Dialogue:',
        'Movie:'
        'Picture:',
        'Sound:',
    ),
}

# It's video track acceptable delta between original chapter time and
# defacto time. If delta > acceptable, try retiming.
# For audio it's acceptable delta between video track and audio track.
# However, output delta maybe more (<= I-frames frequency)
ACCEPT_RETIMING_OFFSETS = {
    'video': timedelta(milliseconds=5000),
    'audio': timedelta(milliseconds=100)
}

# Timestamp input/output usage mkvtoolnix
TIMESTAMP_MKVTOOLNIX = {
    'pattern': r'\d{2}:\d{2}:\d{2}\.\d{9}',
    'hours_place': 2,
    'minutes_place': 2,
    'seconds_place': 2,
    'decimals_place': 9,
}
