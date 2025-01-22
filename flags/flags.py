from pathlib import Path

flags = {}

DEFAULT = {
    'start_dir': Path.cwd(),
    'save_dir': Path.cwd(),

    'locale': 'rus',
    'out_pname': '',
    'out_pname_tail': '',
    'tname': '',
    'tlang': '',

    'lim_search_up': 3,
    'lim_gen': 99999,
    'lim_forced_ttype': 0,
    'lim_default_ttype': 1,
    'lim_enabled_ttype': 99999,
    'lim_forced_signs': 1,

    'range_gen': [1, 99999],

    'rm_chapters': set(),

    'options': [],

    'version': False,
    'pro': False,
    'extended_log': False,
    'search_dirs': True,
    'global_tags': True,
    'chapters': True,
    'sub_charsets': True,
    'files': True,
    'video': True,
    'audio': True,
    'orig_audio': True,
    'subs': True,
    'orig_subs': True,
    'fonts': True,
    'orig_fonts': True,
    'sort_orig_fonts': True,
    'tnames': True,
    'tlangs': True,
    'enableds': True,
    'enabled': True,
    'defaults': True,
    'default': True,
    'forceds': True,
    'forced': False,
    'forced_signs': False,
    't_orders': True,
    'linking': True,
    'opening': True,
    'ending': True,
    'force_retiming': True,

    'for_priority': 'file_first', #dir_first, mix
    'for': {},
}

TYPES = {}
for flag, value in DEFAULT.items():
    if isinstance(value, Path):
        key = 'path'
    elif isinstance(value, bool):
        key = 'bool'
    elif isinstance(value, str):
        key = 'str'
    elif isinstance(value, int):
        key = 'limit'
    elif isinstance(value, list) and len(value) == 2 and all(isinstance(x, int) for x in value):
        key = 'range'
    elif isinstance(value, list):
        key = 'list'
    elif isinstance(value, set):
        key = 'set'
    else:
        key = ''
    TYPES.setdefault(key, set()).add(flag)

STRICT_BOOL = {
    True: {'pro',
           'extended_log',
           'tlangs',
           'tnames',
           'enableds',
           'sort_orig_fonts',
           'defaults',
           'forceds',
           'forced',
           'forced_signs',
           't_orders',
           'sub_charsets',
    }
}
STRICT_BOOL[False] = TYPES['bool'] - STRICT_BOOL[True]

FOR_SEPARATE_FLAGS = TYPES['bool'].union({'tname', 'tlang', 'options'}) - {'version', 'search_dirs'}

MATCHINGS = {
    'part': {'pro_mode': 'pro',
             'directory': 'dir',
             'output': 'out',
             'partname': 'pname',
             'limit': 'lim',
             'generate': 'gen',
             'save_': '',
             'no_': '',
             'add_': '',
             '-': '_',
             'original': 'orig',
             'subtitles': 'subs',
             'attachments': 'fonts',
             'track_orders': 't_orders',
             'track_type': 'ttype',
             'trackname': 'tname',
             'track_name': 'tname',
             'language': 'lang',
             'track_lang': 'tlang',
             'remove': 'rm',
             'directories': 'dirs',
    },

    'full': {'lang': 'tlang',
             'langs': 'tlangs',
             'name': 'tname',
             'names': 'tnames',
             'op': 'opening',
             'ed': 'ending',
             'ver': 'version',
             'v': 'version'
    },
}
