from .audio import Audio
from .chapters import Chapters
from .common import Common
from .subtitles import Subtitles
from .video import Video

from merge_tracks_with_video.tools import check_package

class _MergeRetiming(Audio, Chapters, Common, Subtitles, Video):
    def __init__(self, merge_instance):
        super().__init__()
        self.uids = []
        self.chap_starts = []
        self.chap_ends = []
        self.names = []
        self.remove_idxs = set()

        self.merge = merge_instance
        self.base_video = merge_instance.base_video
        self.execute = merge_instance.execute
        self.get_opt = merge_instance.get_opt
        self.temp_dir = merge_instance.temp_dir
        self.uids_info = merge_instance.files.info.setted_info['uids']

        self.parse_base_chapters()
        self.add_remove_idxs()
        self._set_need_flags()

    def _set_need_flags(self):
        if any(uid for uid in self.uids):
            self.need_retiming = True

        if self.remove_idxs:
            self.need_retiming = True
            self.need_cut = True
        else:
            self.need_cut = False

        if getattr(self, 'need_retiming', None) is None:
            self.need_retiming = False

        self.merge.need_retiming = self.need_retiming

    def _processing_init(self):
        self.video_segments = {}
        self.retimed_video = []
        self.retimed_audio = []
        self.retimed_signs = []
        self.retimed_subtitles = []
        self.indexes = []
        self.sources = {}
        self.lengths = {}
        self.starts = self.chap_starts.copy()
        self.ends = self.chap_ends.copy()
        self.offsets_start = {}
        self.offsets_end = {}

        self.temp_dir = self.merge.temp_dir
        self.base_video = self.merge.base_video
        self.set_opt = self.merge.set_opt
        self.initial_video = self.merge.video_list
        self.initial_audio = self.merge.audio_list
        self.initial_signs = self.merge.signs_list
        self.initial_subtitles = self.merge.subtitles_list
        for opt in ['audio_tracks', 'subtitles_tracks', 'chapters']:
            setattr(self, opt, self.get_opt(opt))

    def processing(self):
        check_package('ffmpeg')
        self._processing_init()
        self.correct_none_times()
        self.fill_retimed_video()
        self.fill_retimed_audio()
        self.fill_retimed_signs_subtitles()

        # Set links to retimed lists in merge
        self.merge.video_list = self.retimed_video
        self.merge.audio_list = self.retimed_audio
        self.merge.signs_list = self.retimed_signs
        self.merge.subtitles_list = self.retimed_subtitles

        self.generate_new_chapters()

    def processing_mismatched_codec_private_data(self):
        self.need_cut = True
        self.set_opt('linked_segments', False, 'global')
        self.add_remove_idxs()

        self.indexes[:] = [
            x for x in self.indexes
            if x not in self.remove_idxs
        ]
        self.video_segments['paths'][:] = [
            x for x in self.video_segments['paths']
            if not (self.remove_idxs & self.video_segments[x])
        ]
        self.update_retimed_video()
        self.fill_retimed_audio()
        self.fill_retimed_signs_subtitles()

        self.generate_new_chapters()

def init(merge_instance):
    instance = _MergeRetiming(merge_instance)
    return instance
