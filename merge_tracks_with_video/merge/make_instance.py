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
        if self.base_video.endswith('.mkv'):
            self.retiming = merge_tracks_with_video.merge.retiming. \
                make_instance.init(self)

        if any(x for x in (
            self.need_retiming, self.audio_list, self.signs_list,
            self.subtitles_list)
        ):
            return True
        else:
            return False

    def _execute_merge(self):
        self.set_orders()
        command = self.get_merge_command()

        msg = '\nGenerating a merged video file using mkvmerge.'
        verbose = not self.verbose is False
        stdout = self.execute(command, exit_on_error=False, verbose=verbose,
                              msg=msg, to_json=self.command_json)
        msg = (
            'The command was executed successfully. The merged video '
            f'file was saved to:\n{self.out_path}'
        )

        if not isinstance(stdout, tuple):
            if self.verbose:
                print(stdout)
            print(msg)
        elif self.processing_errors_and_warnings(stdout[0], msg):
            self._execute_merge()

    def _get_stem_idx(self, stem, base_ftrie):
        if self.idx_str:  # Previos
            idx_str = stem[self.idx_start:self.idx_end]
            if re.fullmatch(r'^[0-9]+$', idx_str):
                self.idx_str = idx_str
                return int(idx_str)

        starts_cnt = len(base_ftrie.starts_with(stem))
        pattern = r'\d+'
        matches = list(re.finditer(pattern, stem))
        for match in reversed(matches):
            _cut_stem = stem[:match.start()]
            if len(base_ftrie.starts_with(_cut_stem)) > starts_cnt:
                self.idx_start = match.start()
                self.idx_end = match.end()
                self.idx_str = stem[self.idx_start:self.idx_end]
                break

        idx = int(self.idx_str) if self.idx_str else 0
        return idx

    def processing(self):
        count_gen = 0
        count_gen_earlier = 0
        def get_opt(x): return self.get_opt(x, 'global')

        start, end = get_opt('range_generate')
        lim_gen = get_opt('limit_generate')
        base_ftrie = self.files.dir_ftrie_pairs[self.files.base_dir]
        stems = self.files.stems.starts_with('')
        stems.sort()

        self.idx_str = ''
        for stem in stems:
            idx = self._get_stem_idx(stem, base_ftrie)
            if idx < start:
                continue
            elif idx > end:
                break
            elif count_gen >= lim_gen:
                break
            elif not self.set_stem_params(stem):
                print(f"Not found video by prefix '{self.stem}'. Skip this.")
                continue
            elif not self._retiming_or_something_else():
                print("Not found external tracks for video "
                      f"'{self.base_video}'. Skip this.")
                continue
            elif self.set_out_path(idx) and os.path.exists(self.out_path):
                print(f"File '{self.out_path}' is already exists. Skip this.")
                count_gen_earlier += 1
                continue

            if self.need_retiming:
                self.retiming.processing()
            self.set_fonts_list()
            self._execute_merge()
            count_gen += 1

        self.count_gen = count_gen
        self.count_gen_earlier = count_gen_earlier

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
