import configparser
import locale
import os
import re
import sys

from .target_parsers import TargetParsers
from . import manager

from merge_tracks_with_video.constants import (
    SETTING_OPTS,
    DEFAULT_OPTS,
    PATTERNS
)
from merge_tracks_with_video.metadata import __config_name__, __package_name__
import merge_tracks_with_video.tools

class _Parse(TargetParsers):
    def __init__(self):
        super().__init__()
        self.target_dict = {}

    def _correct_action_append_arg(self, key, raw_value):
        if (len(raw_value) > 1 and
            any(not isinstance(val, dict) for val in raw_value)
        ):
            print(f"{__package_name__}: error: argument "
                  f"--{key.replace('_', '-')}: received single and multiple "
                  f"values {raw_value}")
            sys.exit(1)

        elif not isinstance(raw_value[0], dict):
            value = raw_value[0]
        else:
            value = {}
            for val in raw_value:
                value.update(val)

        return value

    def _correct_args(self, args, target):
        args_dict = vars(args)

        for x in ['start', 'save']:
            x += '_directory'
            if args_dict.get(x, None) is None:
                args_dict[x] = args_dict.pop(f'pos_{x}', None)

        for key in SETTING_OPTS['action_append']:
            if args_dict[key] is not None:
                value = args_dict[key]
                value = self._correct_action_append_arg(key, value)
                args_dict[key] = value

        return args_dict

    def _parse_args(self, to_parse):
        target = 'global'
        while True:
            target_dict = self.target_dict.setdefault(target, {})
            if target == 'global':
                parser = self.glob_parser
            else:
                parser = self.target_parser
            args = parser.parse_args(to_parse)

            args_dict = self._correct_args(args, target)
            for key in args_dict:
                value = args_dict[key]
                if value is None:
                    pass

                elif key in merge_tracks_with_video.tools.tool_paths:
                    command = [key] + value
                    print(merge_tracks_with_video.tools.execute(
                        command, quiet=False)
                    )
                    sys.exit(0)

                elif not key in SETTING_OPTS['auxiliary']:
                    target_dict[key] = value

            if args.target is None:
                break
            else:
                raw = ''.join(args.target[:1])
                if not raw:
                    target = 'global'
                elif raw in SETTING_OPTS['special_targets']:
                    target = raw
                else:
                    target = os.path.abspath(raw)
                to_parse = args.target[1:]

    def _parse_config(self, path):
        config = configparser.ConfigParser()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config.read_file(f)
        except Exception:
            print(
                f"Error: Incorrect config in the file '{path}'.\n"
                "Please fix or remove the config and re-run the script.")
            sys.exit(1)

        default = DEFAULT_OPTS['global']
        setting = SETTING_OPTS['config']
        sections = config.sections()
        supported = set(default).union(setting['bool_replace_keys'])
        to_parse = []
        for section in sections:
            for key, value in config.items(section):
                lower_key = key.replace('-', '_')

                if lower_key not in supported or '_' in key:
                    print(f"Error: unsupported option '{key}' in the config "
                          f"{path}")
                    sys.exit(1)

                elif lower_key in setting['bool_only']:
                    _value = PATTERNS['bool'].get(value.lower(), None)
                    if _value is None:
                        print("Error: incorrect Bool value for option "
                              f"'{key}' in the config {path}")
                        sys.exit(1)
                    else:
                        manager.set_opt(lower_key, _value)
                        continue

                elif (lower_key in setting['bool_maybe'] and
                      value.lower() in PATTERNS['bool']
                ):
                    _key = setting['bool_replace_keys'].get(
                        lower_key, lower_key)
                    _value = PATTERNS['bool'][value.lower()]
                    manager.set_opt(_key, _value)

                else:
                    to_parse.append(f'--{key}')
                    if key in setting['split']:
                        to_parse.extend(value.split())
                    else:
                        to_parse.append(value)

        self._parse_args(to_parse)

    def configs(self):
        _dir = os.path.abspath(__file__)
        for _ in range(3):
            _dir = os.path.dirname(_dir)

        config_paths = [
            os.path.join(_dir, __config_name__),
            os.path.join(os.getcwd(), __config_name__)
        ]
        for path in config_paths:
            if os.path.isfile(path):
                self._parse_config(path)

    def sys_argv(self):
        self._parse_args(sys.argv[1:])

def _by_locale():
    for element in locale.getlocale():
        loc_words = set(element.split('_'))
        for lang, keys in PATTERNS['languages'].items():
            if keys & loc_words:
                manager.set_opt('locale_language', lang)
                return

def init():
    manager.setted_opts.clear()
    _by_locale()
    parse = _Parse()
    parse.configs()
    parse.sys_argv()

    for target, _dict in parse.target_dict.items():
        manager.setted_opts.setdefault(target, {}).update(_dict)

    glob_opts = manager.setted_opts.get('global', {})
    if ('start_directory' in glob_opts and
        not 'save_directory' in glob_opts
    ):
        glob_opts['save_directory'] = glob_opts['start_directory']

if __name__ == '__main__':
    merge_tracks_with_video.tools.init()
    init()
