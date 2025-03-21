import os

from .directories import Directories
from .prefix_tries import PrefixTries

from constants import EXTS_TUPLE
import files.info.make_instance
import options.manager

class _Fonts():
    def _scan_dir_fonts(self, path):
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    name = entry.name
                    if name.endswith(EXTS_TUPLE['fonts']):
                        yield name

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
        self.get_opt = options.manager.get_opt
        self.set_opt = options.manager.set_opt
        self.skip_file_patterns = self.get_opt('skip_file_patterns')
        self.skip_directory_patterns = self.get_opt('skip_directory_patterns')

        self.find_base_dir()
        self.len_base_dir = len(self.base_dir)
        self.delete_stems_doubles()
        self.set_dir_ftrie_pairs()

        self.info = files.info.make_instance.init(self.base_dir)

def init():
    start_dir = options.manager.get_opt('start_directory')
    instance = _Files(start_dir)
    return instance

if __name__ == '__main__':
    import options.settings
    import tools

    tools.init()
    options.settings.init()
    init()
