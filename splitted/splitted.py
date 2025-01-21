from pathlib import Path

import executor
import flags.merge
import merge.params
import tools.installed
from . import audio, chapters, common, params, subs, video

def check_exist_split():
    file_chapters = Path(merge.params.temp_dir) / 'chapters.xml'
    if file_chapters.exists():
       file_chapters.unlink()
    executor.execute(['mkvextract', str(merge.params.video), 'chapters', str(file_chapters)], get_stdout=False)

    chapters.set_chapters_info(file_chapters)
    params.skips = set()
    common.add_skips()

    if any(uid for uid in params.uids):
        merge.params.mkv_linking = merge.params.mkv_split = True

    if params.skips:
        merge.params.mkv_cutted = merge.params.mkv_split = True

def set_init_files_params():
    params.video = merge.params.video
    params.audio_list = merge.params.audio_list.copy()
    params.subs_list = merge.params.subs_list.copy()

    params.temp_dir = merge.params.temp_dir

    for flg in ['orig_audio', 'orig_subs', 'chapters']:
        setattr(params, flg, flags.merge.bool_flag(flg))

def processing_segments():
    tools.installed.ffmpeg()
    params.segments[''] = {} #clear info about non-uid
    set_init_files_params()

    chapters.correct_chapters_times()
    video.fill_video_segments()
    audio.fill_retimed_audio()
    subs.fill_retimed_subs()

    merge.params.video_list = params.segments_vid
    merge.params.audio_list = params.retimed_audio
    merge.params.subs_list = params.retimed_subs
    chapters.generate_new_chapters()

def processing_codec_error():
    common.add_skips(linking=True)
    params.indexes[:] = [x for x in params.indexes if x not in params.skips]
    params.segments_vid[:] = [x for x in params.segments_vid if not (params.segments_inds[str(x)] & params.skips)]

    audio.fill_retimed_audio()
    subs.fill_retimed_subs()
    chapters.generate_new_chapters()

    merge.params.mkv_cutted = merge.params.rm_linking = True
