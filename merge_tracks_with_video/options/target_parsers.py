import argparse

from .custom_types import CustomTypes

from merge_tracks_with_video.constants import (
    INVERSE_UNSET_ON_PRO,
    SETTING_OPTS,
    TOOLS
)
from merge_tracks_with_video.metadata import __package_name__, __version__

class TargetParsers():
    def __init__(self):
        self.glob_parser = argparse.ArgumentParser(
            prog=__package_name__, add_help=False,
            usage='%(prog)s [start_dir] [save_dir] [options]'
        )
        self._add_glob_args()
        self.target_parser = self._get_target_parser()

    def _add_glob_args(self):
        def add_group(x):
            group = parser.add_argument_group(x)
            return group.add_argument

        ct = CustomTypes()
        parser = self.glob_parser

        add = add_group('File paths options')
        add('pos_start_directory', type=ct.start_directory, nargs='?',
            help=argparse.SUPPRESS
        )
        add('--start-directory', type=ct.start_directory,
            help='Set file search start directory.'
        )
        add('pos_save_directory', type=ct.save_directory, nargs='?',
            help=argparse.SUPPRESS
        )
        add('--save-directory', type=ct.save_directory,
            help='Set merged files save directory.'
        )
        add('-o', '--output', type=ct.output,
            help=(
                "Write to the files 'OUT{episode_number}PUT.mkv' in the "
                "SAVE_DIRECTORY. The OUTPUT format is: OUT[,PUT,...]"
            )
        )
        add('--limit-search-above', type=ct.non_negative_int,
            help=(
                'Set the maximum number of directory levels to search above '
                'the START_DIRECTORY.'
            )
        )
        add('--range-generate', type=ct.range_generate,
            help='Set the range of episode numbers for file processing.'
        )
        add('--limit-generate', type=ct.positive_int,
            help='Set the maximum number of generated files.'
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
        add('--locale-language', type=ct.language_code,
            help='Set priority language for track sort.'
        )
        add('--pro-mode', action='store_true', default=None,
            help='Enable Pro-mode (Inverse default values some options).'
        )


        add = add_group('Inverse in Pro-mode')
        for flag in sorted(INVERSE_UNSET_ON_PRO):
            if not flag.startswith('adding'):
                continue
            key = flag.replace('_', '-')
            hkey = key[7:-1]
            add(f'--{key}', action=argparse.BooleanOptionalAction,
                help=(
                    f'Include or Exclude {hkey} options in mkvmerge commands.'
                    ' (default: Include)'
                )
            )
        add('--sorting-fonts', action=argparse.BooleanOptionalAction,
            help=(
                'Enable or Disable extracting in-files fonts to alphabet '
                'sorting. (default: Enable)'
            )
        )


        add = add_group('Retiming options')
        add('--remove-segments', type=ct.remove_segments,
            help=(
                'Remove segments whose names are listed in REMOVE_SEGMENTS '
                '(format: name0[,name1,...]).'
            )
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


        add = parser.add_argument

        add('--limit-forced-display-flag', type=ct.non_negative_int)
        add('--limit-default-track-flag', type=ct.non_negative_int)
        add('--limit-track-enabled-flag', type=ct.non_negative_int)

        # Usage "Last One Wins" principle similar to mkvmerge behavior
        add('-a', '--audio-tracks', type=ct.tracks)
        add('-A', '--no-audio', action='store_false', default=None,
            dest='audio_tracks')
        add('-d', '--video-tracks', type=ct.tracks)
        add('-D', '--no-video', action='store_false', default=None,
            dest='video_tracks')
        add('-s', '--subtitle-tracks', type=ct.tracks,
            dest='subtitles_tracks')
        add('-S', '--no-subtitles', action='store_false', default=None,
            dest='subtitles_tracks')
        add('-M', '--no-attachments', action='store_false', default=None,
            dest='fonts')
        add('--no-fonts', action='store_false', default=None, dest='fonts')

        # Supports "Accumulate single values" principle, similar to
        # mkvmerge behavior,  where each --track-name can accept a
        # single value (e.g. --track-name 2:name --track-name 3:name).
        # Additionally, it supports passing multiple values in one
        # argument (e.g. --track-name 2:name,3:name).
        add('--track-name', action='append', type=ct.track_name)
        add('--language', action='append', type=ct.language)
        add('--forced-display-flag', '--forced-track', action='append',
            type=ct.track_bool_flag, dest='forced_display_flag')
        add('--default-track-flag', action='append', type=ct.track_bool_flag)
        add('--track-enabled-flag', action='append', type=ct.track_bool_flag)

        add('--specials', nargs=1,
            help='Add other options to mkvmerge commands.')
        add('--target', nargs=argparse.REMAINDER)
        for tool in TOOLS['names']:
            add(f'--{tool}', nargs=argparse.REMAINDER)

        group = parser.add_argument_group('Other options')
        add = group.add_argument
        add('-h', '--help', action='help', help='Show this help.')
        add('-V', '--version', action='version',
            version=f'{__package_name__} {__version__}',
            help='Show version information.')

    def _get_target_parser(self):
        target_parser = argparse.ArgumentParser(
            prog=__package_name__, add_help=False,
            usage='%(prog)s [start_dir] [save_dir] [options]'
        )
        arguments = self.glob_parser._actions
        for arg in arguments:
            if arg.dest not in SETTING_OPTS['exclude_in_target']:
                target_parser._add_action(arg)

        target_parser.add_argument('--no-files', action='store_false',
                                   default=None, dest='files')
        return target_parser
