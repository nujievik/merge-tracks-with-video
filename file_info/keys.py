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

    'subs': {
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

    'retime_subs': {
        '.ass'
    },

    'single_track': {
        '.srt'
    },
}
EXTENSIONS['video'] = EXTENSIONS['container'].union(EXTENSIONS['video'])
EXTENSIONS['audio'] = EXTENSIONS['container'].union(EXTENSIONS['audio'])

KEYS = {
    # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.default_values
    'default_matroska': {
        'language': 'eng'
    },

    'skip_dir': {
        '__temp_files__',
        'bonus',
        'бонус',
        'special',
        'bdmenu',
        'commentary',
        'creditless',
        'nc',
        'nd',
        'op',
        'pv'
    },

    'skip_file': {
        '_merged_',
        '_cutted_',
        '_added_',
        '_replaced_',
        '_temp_'
    },

    'signs': {
        'надписи',
        'signs'
    },

    'lang': {

        'rus': {
            'надписи',
            'субтитры',
            'russian',
            'rus',
            'ru'
        },

        'eng': {
            'english',
            'eng',
            'en'
        },

        'jpn': {
            'japanese',
            'jpn',
            'ja',
            'jp'
        },
    },
}
