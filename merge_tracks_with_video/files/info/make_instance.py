from .by_ffprobe import ByFfprobe
from .by_mkvtools import ByMkvtools
from .char_encoding import CharEncoding
from .path_ops import PathOps
from .track import Track

import merge_tracks_with_video.tools

class _FilesInfo(ByFfprobe, ByMkvtools, CharEncoding, PathOps, Track):
    def __init__(self, files_instance):
        super().__init__()
        self.base_dir = files_instance.base_dir
        self.get_opt = files_instance.get_opt
        self.len_base_dir = len(self.base_dir)
        self.stem = ''
        self.setted_info = {}
        self.tools = merge_tracks_with_video.tools

def init(files_instance):
    instance = _FilesInfo(files_instance)
    return instance

if __name__ == '__main__':
    import merge_tracks_with_video.files.make_instance
    import merge_tracks_with_video.options.manager
    import merge_tracks_with_video.options.settings

    merge_tracks_with_video.tools.init()
    options.settings.init()
    files_instance = merge_tracks_with_video.files.make_instance.init()
    init(files_instance)
