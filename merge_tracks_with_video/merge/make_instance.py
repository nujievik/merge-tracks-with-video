import os
import re

from .attachs import Attachs
from .errors import Errors
from .command import Command
from .orders import Orders
from .params import Params

import merge_tracks_with_video.merge.retiming.make_instance

class _Merge(Attachs, Errors, Command, Orders, Params):
    def __init__(self, files_instance, temp_dir):
        super().__init__()
        self.files = files_instance
        self.temp_dir = temp_dir
        self.set_common_params()

    def _retiming_or_something_else(self):
        if self.base_video[-4:].lower() == '.mkv':
            self.retiming = merge_tracks_with_video.merge.retiming. \
                make_instance.init(self)

        if any(x for x in (
            self.need_retiming, self.audio_list, self.signs_list,
            self.subtitles_list)
        ):
            return True
        else:
            return False

    def _get_stem_idx(self, stem, stems_trie):
        if self.idx_str:  # Previos
            idx_str = stem[self.idx_start:self.idx_end]
            if re.fullmatch(r'^[0-9]+$', idx_str):
                self.idx_str = idx_str
                return int(idx_str)

        starts_cnt = len(stems_trie.starts_with(stem))
        pattern = r'\d+'
        matches = list(re.finditer(pattern, stem))
        for match in reversed(matches):
            _cut_stem = stem[:match.start()]
            if len(stems_trie.starts_with(_cut_stem)) > starts_cnt:
                self.idx_start = match.start()
                self.idx_end = match.end()
                self.idx_str = stem[self.idx_start:self.idx_end]
                break

        return int(self.idx_str) if self.idx_str else 0

    def processing(self):
        def execute_merge():
            self.set_orders()
            command = self.get_merge_command()

            msg = '\nGenerating a merged video file using mkvmerge.'
            verbose = not self.verbose is False
            stdout = self.execute(
                command, exit_on_error=False, verbose=verbose, msg=msg,
                to_json=self.command_json
            )
            msg = (
                f'The command was executed successfully. The merged '
                f'video file was saved to:\n{self.out_path}'
            )

            if not isinstance(stdout, tuple):
                if self.verbose:
                    print(stdout)
                if verbose:
                    print(msg)
                return True
            elif self.processing_errors_and_warnings(stdout[0], msg):
                execute_merge()  # Repeat

        def get_opt(x):
            return self.get_opt(x, 'global')

        count_gen = 0
        lim_gen = get_opt('limit_generate')
        start, end = get_opt('range_generate')
        stems_trie = self.files.stems
        stems = stems_trie.starts_with('')
        stems.sort()
        verbose = self.verbose

        self.idx_str = ''
        # Init False on condition stem.startswith(prev_stem)
        prev_stem = os.sep * 10
        for stem in stems:
            if stem.startswith(prev_stem):
                continue
            prev_stem = stem
            idx = self._get_stem_idx(stem, stems_trie)
            if idx < start:
                continue
            elif idx > end:
                break
            elif count_gen >= lim_gen:
                break
            elif not self.set_stem_params(stem):
                if verbose:
                    print(f"Not found video on prefix '{stem}'. Skip this.")
                continue
            elif not self._retiming_or_something_else():
                if verbose:
                    print(f"Not found external tracks for video "
                          f"'{self.base_video}'. Skip this.")
                continue
            elif self.set_out_path(idx) and os.path.exists(self.out_path):
                if verbose is not False:
                    print(f"File '{self.out_path}' is already exists. Skip "
                          f"this.")
                continue

            if self.need_retiming:
                self.retiming.processing()
            self.set_fonts_list()

            if execute_merge():
                count_gen += 1

        self.count_gen = count_gen

def init(files_instance, temp_dir):
    instance = _Merge(files_instance, temp_dir)
    return instance

if __name__ == '__main__':
    import shutil
    import uuid

    import merge_tracks_with_video.files.make_instance
    import merge_tracks_with_video.options.settings
    import merge_tracks_with_video.tools

    merge_tracks_with_video.tools.init()
    merge_tracks_with_video.options.settings.init()
    files_instance = merge_tracks_with_video.files.make_instance.init()

    save_dir = files_instance.get_opt('save_directory')
    temp_dir = os.path.join(
        save_dir, f'__temp_files__.{str(uuid.uuid4())[:8]}')
    try:
        _merge = init(files_instance, temp_dir)
        _merge.processing()
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
