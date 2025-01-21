from pathlib import Path

import file_info.mkvtools
from flags import get_flag
from . import find_ext, directories
from .files import files, EXTENSIONS

def rm_duplicates_fonts_sort(fonts_list):
    cleaned_list = []
    stem_list = []
    stems = set()

    for font in fonts_list:
        if not font.stem in stems:
            stems.add(font.stem)
            stem_list.append(font.stem)

    stem_list.sort(key=str.lower)
    for stem in stem_list:
        for font in fonts_list:
            if font.stem == stem:
                cleaned_list.append(font)
                break

    return cleaned_list

def collect_files(dirs):
    for group in ['audio', 'subs', 'fonts']:
        if dirs['audio'] or dirs['subs']:
            search_dir = dirs[group]
            recursive = False
        else:
            search_dir = get_flag.flag('start_dir')
            recursive = True

        files[group] = find_ext.find_ext_files(search_dir, EXTENSIONS[group], recursive=recursive)

    if files['fonts']:
        files['fonts'] = rm_duplicates_fonts_sort(files['fonts'])

def clear_non_video_pair():
    temp = {}
    temp['video'] = []
    for group in ['audio', 'subs']:
        temp[group] = {}

    for video in files['video']:
        tmp = {}
        skip_video = save_video = track_video = False

        for group in ['audio', 'subs']:
            for fpath in files[group]:
                if str(video) == str(fpath): #skip any
                    if track_video or file_info.mkvtools.file_has_video_track(video):
                        track_video = True
                        continue
                    else:
                        skip_video = True
                        break

                if video.stem in fpath.stem or fpath.stem in video.stem:
                    tmp.setdefault(group, []).append(fpath)
                    save_video = True

            if skip_video:
                break

        if skip_video:
            continue

        elif save_video:
            temp['video'].append(video)
            for group in ['audio', 'subs']:
                if tmp.get(group, []):
                    temp[group][str(video)] = tmp[group]

    files.update(temp)

def find_all_files():
    directories.set_directories()
    dirs = files['directories']

    search_dir = dirs['video'] if dirs.get('video', None) else get_flag.flag('start_dir')
    files['video'] = find_ext.find_ext_files(search_dir, EXTENSIONS['video'])
    if not files['video']:
        return

    collect_files(dirs)
    clear_non_video_pair()

    if not files['video']: #try find .mkv for processing splitting
        files['video'] = find_ext.find_ext_files(get_flag.flag('start_dir'), '.mkv')
