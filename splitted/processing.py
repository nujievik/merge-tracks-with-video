import os

import executor
import merge.params
import options.manager
import third_party_tools
from . import audio, chapters, common, params, subtitles, video

def check_exist_split():
    file_chapters = os.path.join(merge.params.temp_dir, 'chapters.xml')
    if os.path.exists(file_chapters):
        os.remove(file_chapters)
    command = ['mkvextract', merge.params.base_video,
               'chapters', file_chapters]
    executor.execute(command, get_stdout=False)

    chapters.set_chapters_info(file_chapters)
    params.skips = set()
    common.add_skips()

    if any(uid for uid in params.uids):
        merge.params.mkv_linking = merge.params.mkv_split = True

    if params.skips:
        merge.params.mkv_cutted = merge.params.mkv_split = True

def set_init_files_params():
    params.temp_dir = merge.params.temp_dir
    params.base_video = merge.params.base_video
    params.audio_list = merge.params.audio_list.copy()
    params.subtitles_list = merge.params.subtitles_list.copy()

    for flg in {'orig_audio', 'orig_subtitles', 'chapters'}:
        setattr(params, flg, options.manager.get_merge_flag(flg))

def processing_segments():
    third_party_tools.check_installation('ffmpeg')
    params.segments[''] = {}  # Clear info about non-uid
    set_init_files_params()

    chapters.correct_chapters_times()
    video.fill_video_segments()
    audio.fill_retimed_audio()
    subtitles.fill_retimed_subtitles()

    merge.params.video_list = params.segments_vid
    merge.params.audio_list = params.retimed_audio
    merge.params.subtitles_list = params.retimed_subtitles
    chapters.generate_new_chapters()

def processing_codec_error():
    common.add_skips(linking=True)
    params.indexes[:] = [x for x in params.indexes if x not in params.skips]
    params.segments_vid[:] = [
        x for x in params.segments_vid
        if not (params.segments_inds[x] & params.skips)
    ]

    audio.fill_retimed_audio()
    subtitles.fill_retimed_subtitles()
    chapters.generate_new_chapters()

    merge.params.mkv_cutted = merge.params.rm_linking = True
