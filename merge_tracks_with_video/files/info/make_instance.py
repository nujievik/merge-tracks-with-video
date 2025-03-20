from .by_ffprobe import ByFfprobe
from .by_mkvtools import ByMkvtools
from .char_encoding import CharEncoding
from .path_ops import PathOps
from .track import Track

class _FilesInfo(ByFfprobe, ByMkvtools, CharEncoding, PathOps, Track):
    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = base_dir
        self.len_base_dir = len(self.base_dir)
        self.stem = ''
        self.setted = {}

def init(base_dir):
    instance = _FilesInfo(base_dir)
    return instance

if __name__ == '__main__':
    import options.manager
    import options.settings
    import tools

    tools.init()
    options.settings.init()
    base_dir = options.manager.get_opt('start_directory')
    init(base_dir)
