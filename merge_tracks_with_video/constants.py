import os
from datetime import timedelta

ACCURACY_TIMEDELTA = 6
SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60

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

ARGUMENTS = {
    'action_append': {
        'track_name',
        'language',
        'forced_display_flag',
        'default_track_flag',
        'track_enabled_flag',
    },

    'auxiliary': {
        'pos_start_directory',
        'pos_save_directory',
        'target',
    },

    'config': {
        'bool_maybe': {
            'audio_tracks',
            'video_tracks',
            'subtitle_tracks',
        },

        'bool_only': {
            'verbose',
            'pro_mode',
            'search_above',
            'linked_segments',
            'opening',
            'ending',
            'force_retiming',
            'fonts',
            'sorting_fonts',
        },

        'bool_replace_keys': {
            'subtitle_tracks': 'subtitles_tracks',
        },

        'split': {
            'target',
        },
    },

    'exclude_in_target': {
        'pos_start_directory',
        'save_directory',
        'pos_save_directory',
        'start_directory',
        'output',
        'verbose',
        'quiet',
        'locale_language',
        'search_above',
        'range_generate',
        'limit_generate',
        'limit_search_above',
        'remove_segments',
        'linked_segments',
        'opening',
        'ending',
        'force_retiming',
    },
}
ARGUMENTS['config']['split'].update({x for x in TOOLS['names']})

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

DEFAULT_OPTS = {
    'global': {
        'start_directory': os.getcwd(),
        'save_directory': os.getcwd(),

        'output': None,  # By default usage orig name + suffixes
        'verbose': None,
        'pro_mode': False,
        'search_above': True,
        'locale_language': 'rus',
        'range_generate': [0, 9999999],

        'limit_generate': 9999999,
        'limit_search_above': 3,
        'limit_forced': 0,
        'limit_default': 1,
        'limit_enabled': 9999999,
        'limit_sorting_files': 10000,
        #'limit_tracks': 9999999,

        'remove_segments': set(),
        'linked_segments': True,
        'opening': True,
        'ending': True,
        'force_retiming': True,

        'audio_tracks': True,
        'video_tracks': True,
        'signs_tracks': True,
        'subtitles_tracks': True,
        'fonts': True,
        'sorting_fonts': True,
        'chapters': True,

        'track_name': '',
        'language': '',
        'forced_display_flag': False,
        'default_track_flag': True,
        'track_enabled_flag': True,

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

        'flag_track_order': True,
    },

    'signs': {
        'limit_forced': 1,  # Limit 1 but flag disabled by default
        'forced_display_flag': False,
    },
}

INVERSE_UNSET_ON_PRO = {}


#
# Files constants
#

CHUNK_SIZE_READ = 1024 * 1024  # 1 MiB

EXTS_SET = {
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
EXTS_SET['video'].update(EXTS_SET['container'])
EXTS_SET['audio'].update(EXTS_SET['container'])
EXTS_SET['total_wo_fonts'] = EXTS_SET['video'].union(
    EXTS_SET['audio'], EXTS_SET['subtitles'])

EXTS_TUPLE = {group: tuple(exts)
              for group, exts in EXTS_SET.items()}

# The Matroska(tm) specification states that some elements have a
# default value. Source: (https://mkvtoolnix.download/doc/mkvmerge.html
# #mkvmerge.default_values)
MATROSKA_DEFAULT = {
    'language': 'eng',
}


#
# Retiming constants
#

ASS_SPECS = {
    'events_idx_start': 1,

    'events_prefixes': (
        'Dialogue:',
        'Comment:',
        'Picture:',
        'Sound:',
        'Movie:'
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

SHORT_NAMES_FLAG_SEGMENTS = {
    'opening': 'op',
    'ending': 'ed',
}
