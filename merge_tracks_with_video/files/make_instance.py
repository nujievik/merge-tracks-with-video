import os

from .directories import Directories
from .prefix_tries import PrefixTries

from merge_tracks_with_video.constants import EXTS
import merge_tracks_with_video.files.info.make_instance
import merge_tracks_with_video.options.manager

class _Fonts():
    def _scan_dir_fonts(self, path):
        exts = EXTS['fonts']
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_symlink() or not entry.is_file():
                    continue
                name = entry.name
                if not os.path.splitext(name)[1] in exts:
                    continue
                yield name

    def iterate_dir_fonts(self):
        _scan_dir_fonts = self._scan_dir_fonts
        for _dir in self.dir_ftrie_pairs:
            fonts = _scan_dir_fonts(_dir)
            yield (_dir, fonts)

class _Files(Directories, PrefixTries, _Fonts):
    def __init__(self, start_dir):
        super().__init__()
        self.start_dir = start_dir
        self.dir_ftrie_pairs = {}
        self.get_opt = merge_tracks_with_video.options.manager.get_opt
        self.set_opt = merge_tracks_with_video.options.manager.set_opt
        self.skip_file_patterns = self.get_opt('skip_file_patterns')
        self.skip_directory_patterns = self.get_opt('skip_directory_patterns')

        self.set_base_dir()
        self.len_base_dir = len(self.base_dir)
        self.stems = self.get_stems_trie(self.base_dir)
        if not self.stems.root.children:
            return

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
