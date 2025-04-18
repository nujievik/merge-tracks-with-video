import argparse

from .custom_types import CustomTypes

from merge_tracks_with_video.constants import (
    DEFAULT_OPTS,
    INVERSE_UNSET_ON_PRO,
    TOOLS
)
from merge_tracks_with_video.metadata import __package_name__, __version__

class TargetParsers():
    def __init__(self):
        self.glob_parser = argparse.ArgumentParser(
            prog=__package_name__, add_help=False,
            usage='%(prog)s [start_dir] [save_dir] [options]'
        )
        target_dests = self._add_glob_args()
        self._set_target_parser(target_dests)

    def _add_glob_args(self):
        ct = CustomTypes()
        default = DEFAULT_OPTS['global']
        parser = self.glob_parser

        def add_group(x):
            group = parser.add_argument_group(x)
            return group.add_argument

        add = add_group('File paths options')
        add('pos_start_directory', type=ct.start_directory, nargs='?',
            help=argparse.SUPPRESS
        )
        add('--start-directory', type=ct.start_directory,
            metavar='<start_dir>',
            help=(
                f'Sets file search start directory. Default: cwd '
                f'({default['start_directory']}).'
            )
        )
        add('pos_save_directory', type=ct.save_directory, nargs='?',
            help=argparse.SUPPRESS
        )
        add('--save-directory', type=ct.save_directory, metavar='<save_dir>',
            help=(
                "Sets merged files save directory. Default: subdirectory "
                "'merged' in the start directory."
            )
        )
        add('-o', '--output', type=ct.output, metavar='out[,pu,t,...]',
            help=(
                "Write to the files 'out{episode_number}put.mkv' in the "
                "save directory, where {episode_number} is the number "
                "extracted from the source file name, or empty if no number "
                "is present. Default: video name + suffixes what's done."
            )
        )
        add('--range-generate', type=ct.range_generate, metavar='[n][,m]',
            help='Sets the range n-m of episode numbers for file processing.'
        )
        add('--limit-generate', type=ct.positive_int, metavar='<n>',
            help='Sets the maximum number of generated files.'
        )
        add('--limit-search-above', type=ct.non_negative_int, metavar='<n>',
            help=(
                f'Sets the maximum number of directory levels to search '
                f'above the start directory. Default: '
                f'{default['limit_search_above']}.'
            )
        )
        add('--limit-check-files', type=ct.positive_int, metavar='<n>',
            help=(
                f'Sets the maximum number of files with track extensions '
                f'to check for prefix matches during the search above. '
                f'Default: {default['limit_check_files']}.'
            )
        )
        add('--skip-file-patterns', type=ct.set_patterns, metavar='<n,m,...>',
            help=(
                f'Sets skip file patterns on file names (case sensitive). '
                f'Default: {', '.join(sorted(default['skip_file_patterns']))}'
            )
        )
        add('--skip-directory-patterns', type=ct.set_patterns,
            metavar='<n,m,...>',
            help=(
                f'Sets skip directory patterns on words in relative '
                f'directory path (relative about topmost file directory; '
                f'case insensitive). Default: '
                f'{', '.join(sorted(default['skip_directory_patterns']))}'
            )
        )


        add = add_group('Global options')
        add('-v', '--verbose', action='store_true', default=None,
            help='Increase verbosity.'
        )
        add('-q', '--quiet', action='store_false', default=None,
            dest='verbose', help='Suppress status output.'
        )
        add('--continue-on-error', action='store_true', default=None,
            help=(
                'Continue merging the next files even if any of the current '
                'files encounter an error.'
            )
        )
        add('--locale-language', type=ct.language_code, metavar='<lang>',
            help='Sets priority language for track sort.'
        )
        add('--pro-mode', action='store_true', default=None,
            help='Enable Pro-mode (Inverse default values some options).'
        )


        add = add_group('Inverse on Pro-mode')
        for x in sorted(INVERSE_UNSET_ON_PRO):
            if not x.startswith('adding'):
                continue
            key = '--' + x.replace('_', '-')
            in_help = key[9:-1]
            add(key, action=argparse.BooleanOptionalAction,
                help=(
                    f'Include or Exclude {in_help} options in mkvmerge '
                    'commands. Default: Include.'
                )
            )
        add('--sorting-fonts', action=argparse.BooleanOptionalAction,
            help=(
                'Enable or Disable extracting in-files fonts to alphabet '
                'sorting. Default: Enable.'
            )
        )


        add = add_group('Retiming options')
        add('--remove-segments', type=ct.set_patterns,
            metavar='<n,m,...>',
            help='Remove segments whose names are listed in n,m etc.'
        )
        add('--no-linked-segments', action='store_false', default=None,
            dest='linked_segments', help='Remove linked segments.'
        )
        add('--no-force-retiming', action='store_false', default=None,
            dest='force_retiming', help=(
                'Disable retiming of in-video audio and subtitle tracks when '
                'linked segments are not inside the main video segment.'
            )
        )


        add = add_group('Target options')
        non_target_dests = {x.dest for x in parser._actions}

        add('--target', nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
        add('--target <any_target> [options]', action='help',
            help=(
                'Sets the following options to any target. Supported '
                'targets: (any file or directory, file groups: audio, video, '
                'signs, subtitles, or global). Default: global.'
            )
        )
        add('--target <non_global_target> --no-files', action='help',
            help='Exclude non global target files from merge.'
        )
        for x in ['audio', 'video', 'subtitles']:
            k = x[:1] if x[:1] != 'v' else 'd'
            k = (f'-{k}', f'-{k.upper()}')
            key = x[:-1] if x[-1:] == 's' else x
            key = (f'--{key}-tracks', f'--no-{x}')
            dest = f'{x}_tracks'

            # Usage "Last One Wins" principle similar to mkvmerge
            # behavior
            add(k[0], key[0], type=ct.tracks, dest=dest,
                metavar='<n,m,...>',
                help=f'Copy {x} tracks n,m etc. Default: copy all {x} tracks.'
            )
            add(k[1], key[1], action='store_false', default=None, dest=dest,
                help=f"Don't copy any {x} track."
            )
        add('-M', '--no-attachments', action='store_false', default=None,
            dest='fonts', help="Don't copy any attachment."
        )
        add('--no-fonts', action='store_false', default=None, dest='fonts',
            help="Don't copy any font."
        )
        add('--no-chapters', action='store_false', default=None,
            dest='chapters', help="Don't keep chapters."
        )
        # Supports "Accumulate single values" principle, similar to
        # mkvmerge behavior,  where each --track-name can accept a
        # single value (e.g. --track-name 2:name --track-name 3:name).
        # Additionally, it supports passing multiple values in one
        # argument (e.g. --track-name 2:name,3:name).
        for x in ['default-track', 'forced-display', 'track-enabled']:
            key = f'--{x}-flag'
            limit_key = f'--limit-{x}-flag'
            limit_dest = limit_key[2:].replace('-', '_')
            in_help = f'"{' '.join(x.split('-'))}" flag'

            add(key, action='append', type=ct.track_bool_flag,
                metavar='<TID[:bool][,TID[:bool],...]> | True | False',
                help=(
                    f'Sets the {in_help} for these tracks or forces it not '
                    'to be present if bool is 0. Alternatively, you may use '
                    'a single True|False value without TID prefixes.'
                )
            )
            add(limit_key, type=ct.non_negative_int, metavar='<n>',
                help=(f'Sets the bool limit for the {key[2:]} separately for '
                      'each track group (audio, video, signs, subtitles). '
                      'All bool value exceeding the limit will be set to 0. '
                      f'Default limit: {default[limit_dest]}.'
                )
            )
        # Mkvmerge also usage hidden --forced-track as alternative
        # --forced-display-flag
        add('--forced-track', action='append', type=ct.track_bool_flag,
            dest='forced_display_flag', help=argparse.SUPPRESS
        )
        for x in ['track-name', 'language']:
            _meta = 'name' if x.startswith('t') else 'lang'
            dest = x.replace('-', '_')
            add(f'--{x}', action='append', type=getattr(ct, dest),
                metavar=f'<TID:{_meta}[,TID:{_meta},...]> | {_meta}',
                help=(
                    f'Sets the {x} for these tracks. Alternatively, you may '
                    f'use a single {_meta} value without TID prefixes.'
                )
            )
        add('--specials', type=ct.specials, metavar='<options>',
            help='Sets unpresented mkvmerge options.'
        )

        target_dests = {x.dest for x in parser._actions}.difference(
            non_target_dests)


        add = add_group('Other options')
        for x in sorted(TOOLS['names']):
            add(f'--{x}', nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
            add(f'--{x} [options]', action='help',
                help=f'Calls the {x} with the following options.'
            )

        add('-h', '--help', action='help', help='Show this help.')
        add('-V', '--version', action='version',
            version=f'{__package_name__} {__version__}',
            help='Show version information.')

        return target_dests

    def _set_target_parser(self, target_dests):
        parser = argparse.ArgumentParser(
            prog=__package_name__, add_help=False,
            usage='%(prog)s [start_dir] [save_dir] [options]'
        )
        group = parser.add_argument_group('Target options')
        for arg in self.glob_parser._actions:
            if arg.dest in target_dests:
                group._add_action(arg)
        group.add_argument(
            '--no-files', action='store_false', default=None, dest='files',
            help=argparse.SUPPRESS
        )
        other_group = parser.add_argument_group('Other options')
        other_group.add_argument(
            '-h', '--help', action='help', help='Show this help.'
        )
        self.target_parser = parser
