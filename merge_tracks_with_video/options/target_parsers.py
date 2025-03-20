import argparse

from .custom_types import CustomTypes

from constants import ARGUMENTS
from metadata import __package_name__, __version__
import tools

class TargetParsers():
    def __init__(self):
        self.glob_parser = argparse.ArgumentParser(
            prog=__package_name__,
            usage='%(prog)s [start_dir] [save_dir] [options]'
        )
        self._add_glob_args()
        self.target_parser = self._get_target_parser()

    def _add_glob_args(self):
        ct = CustomTypes()
        add = self.glob_parser.add_argument

        add('pos_start_directory', type=ct.start_directory, nargs='?',
            help='Set start directory')
        add('--start-directory', type=ct.start_directory,
            help='Set start directory')
        add('pos_save_directory', type=ct.save_directory, nargs='?',
            help='Set save directory')
        add('--save-directory', type=ct.save_directory,
            help='Set save directory')

        add('-V', '--version', action='version',
            version=f'{__package_name__} {__version__}')
        add('-o', '--output', type=ct.output)
        add('-v', '--verbose', action='store_true', default=None,
            help='Increase verbosity')
        add('-q', '--quiet', action='store_false', default=None,
            dest='verbose', help='Suppress status output')
        add('--pro-mode', action='store_true', default=None,
            help='Enable Pro mode')
        add('--no-search-above', action='store_false', default=None,
            dest='search_above')
        add('--locale-language', type=ct.language_code,
            help='Set Priority lang for track sort')
        add('--range-generate', type=ct.range_generate)

        add('--limit-generate', type=ct.positive_int)
        add('--limit-search-above', type=ct.non_negative_int)
        add('--limit-forced', type=ct.non_negative_int)
        add('--limit-default', type=ct.non_negative_int)
        add('--limit-enabled', type=ct.non_negative_int)

        add('--remove-segments', type=ct.remove_segments)
        add('--no-linked-segments', action='store_false', default=None,
            dest='linked_segments')
        add('--no-opening', action='store_false', default=None, dest='opening')
        add('--no-ending', action='store_false', default=None, dest='ending')
        add('--no-force-retiming', action='store_false', default=None,
            dest='force_retiming')

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
        add('--no-sorting-fonts', action='store_false', default=None,
            dest='sorting_fonts')

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
            help='Add other options to mkvmerge command')
        add('--target', nargs=argparse.REMAINDER)
        for tool in tools.tool_paths:
            add(f'--{tool}', nargs=argparse.REMAINDER)

    def _get_target_parser(self):
        target_parser = argparse.ArgumentParser(
            prog=__package_name__, add_help=False,
            usage='%(prog)s [start_dir] [save_dir] [options]'
        )
        arguments = self.glob_parser._actions
        for arg in arguments:
            if arg.dest not in ARGUMENTS['exclude_in_target']:
                target_parser._add_action(arg)

        target_parser.add_argument('--no-files', action='store_false',
                                   default=None, dest='files')
        return target_parser
