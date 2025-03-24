import os

from .directories import Directories
from .prefix_tries import PrefixTries

from merge_tracks_with_video.constants import EXTS, EXTS_LENGTHS
import merge_tracks_with_video.files.info.make_instance
import merge_tracks_with_video.options.manager

class _Fonts():
    def _scan_dir_fonts(self, path):
        lengths = EXTS_LENGTHS['fonts']
        exts = EXTS['fonts']
        with os.scandir(path) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                name = entry.name
                for length in lengths:
                    if name[-length:] in exts:
                        yield name
                        break

    def iterate_dir_fonts(self):
        for _dir in self.dir_ftrie_pairs:
            fonts = self._scan_dir_fonts(_dir)
            yield (_dir, fonts)

class _Files(Directories, PrefixTries, _Fonts):
    def __init__(self, start_dir):
        super().__init__()
        self.dir_ftrie_pairs = {}
        self.sep = os.sep
        self.start_dir = self.ensure_end_sep(start_dir)
        self.get_opt = merge_tracks_with_video.options.manager.get_opt
        self.set_opt = merge_tracks_with_video.options.manager.set_opt
        self.skip_file_patterns = self.get_opt('skip_file_patterns')
        self.skip_directory_patterns = self.get_opt('skip_directory_patterns')

        self.find_base_dir()
        self.len_base_dir = len(self.base_dir)
        self.delete_stems_doubles()
        self.set_dir_ftrie_pairs()

        self.info = merge_tracks_with_video.files.info.make_instance.init(
            self)

def init():
    start_dir = merge_tracks_with_video.options.manager.get_opt(
        'start_directory')
    instance = _Files(start_dir)
    return instance

if __name__ == '__main__':
    import merge_tracks_with_video.options.settings
    import merge_tracks_with_video.tools

    merge_tracks_with_video.tools.init()
    merge_tracks_with_video.options.settings.init()
    init()
