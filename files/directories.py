from pathlib import Path

from . import find_ext
from merge import orders
import file_info.mkvtools
from flags import get_flag
from .files import files, EXTENSIONS

def check_video(video, check_dir):
    if video.suffix not in EXTENSIONS['container']:
        return True
    elif str(video.parent) != str(check_dir):
        return True
    elif file_info.mkvtools.file_has_video_track(video):
        return True

def find_videodir_up(start_dir, extensions):
    for filepath in find_ext.find_ext_files(start_dir, extensions):
        search_dir = start_dir

        for lvl in range(0, get_flag.flag('lim_search_up') + 1):
            for video in find_ext.find_ext_files(search_dir, EXTENSIONS['video'], search_name=filepath.stem):
                if str(video) == str(filepath):
                    continue

                if check_video(video, start_dir):
                    return video.parent

            search_dir = search_dir.parent

def find_dir_by_match_filenames(video_list, search_dir, recursive=False, first=True):
    founds = []
    str_founds = set()

    for video in video_list:
        for found in find_ext.find_ext_files(search_dir, EXTENSIONS['subs'], video.stem, recursive):
            if str(found) == str(video) or str(found.parent) in str_founds:
                continue

            if check_video(video, search_dir):
                if first:
                    return found.parent

                founds.append(found.parent)
                str_founds.add(str(found.parent))

    return founds if founds else None

def find_subsdir_by_sort(video_list, dirs):
    found_dirs = find_dir_by_match_filenames(video_list, dirs['video'], recursive=True, first=False)
    found_subs = []
    for sdir in found_dirs:
        found_subs.extend(find_ext.find_ext_files(sdir, EXTENSIONS['subs'], search_name=video_list[0].stem))

    if found_subs:
        orders.params.video = video_list[0]
        orders.params.locale = get_flag.flag('locale')

        tmp_info = orders.set_files_info(filepaths=found_subs, filegroup='subs', trackgroups=['subs'])
        orders.set_files_order(tmp_info)

        return orders.params.info['filepaths'][0].parent

def find_subsdir_after_audiodir(dirs):
    video_list = find_ext.find_ext_files(dirs['video'], EXTENSIONS['video'])

    if str(dirs['video']) == str(dirs['audio']):
        return find_dir_by_match_filenames(video_list, dirs['audio'])

    for search_dir in [dirs['audio'], dirs['video']]:
        subs_dir = find_dir_by_match_filenames(video_list, search_dir)
        if subs_dir:
            return subs_dir

    return find_subsdir_by_sort(video_list, dirs)

def find_fontdir(dirs):
    for search_dir in [dirs['subs'], dirs['subs'].parent]:
        fonts = find_ext.find_ext_files(search_dir, EXTENSIONS['fonts'], recursive=True)
        if fonts:
            return fonts[0].parent

def set_directories():
    dirs = files.setdefault('directories', {})
    for key in ['video', 'audio', 'subs', 'fonts']:
        dirs[key] = None

    start_dir = get_flag.flag('start_dir')

    dirs['video'] = find_videodir_up(start_dir, EXTENSIONS['audio'])
    if dirs['video']:
        dirs['audio'] = start_dir
        dirs['subs'] = find_subsdir_after_audiodir(dirs)

    else:
        dirs['video'] = find_videodir_up(start_dir, EXTENSIONS['subs'])
        if dirs['video']:
            dirs['subs'] = start_dir

    if dirs['subs']: #find fontdir if found subsdir
        dirs['fonts'] = find_fontdir(dirs)
