EXTENSIONS = {
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

    'mkvtools_supported': {
        '.mka',
        '.mks',
        '.mkv',
        '.webm'
    },

    'retime_subtitles': {
        '.ass'
    },

    'single_track': {
        '.srt'
    },
}
EXTENSIONS['video'].update(EXTENSIONS['container'])
EXTENSIONS['audio'].update(EXTENSIONS['container'])

SUFFIXES = {}
total = set()
for group, exts in EXTENSIONS.items():
    SUFFIXES[group] = tuple(exts)
    total.update(exts)
SUFFIXES['total_wo_fonts'] = tuple(total - EXTENSIONS['fonts'])

# https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.default_values
MATROSKA_DEFAULT = {
    'language': 'eng'
}

PATTERNS = {
    'skip_dir': {
        '__temp_files__',
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
        'бонус',
    },

    'skip_file': {
        '_added_',
        '_cutted_',
        '_merged_',
        '_replaced_',
    },

    'signs': {
        'signs',
        'надписи',
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
}
