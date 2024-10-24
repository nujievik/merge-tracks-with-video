"""
generate-video-with-these-files-v0.4.0
This program is part of the generate-video-with-these-files-script repository
Licensed under GPL-3.0. See LICENSE file for details.
Author: nujievik Email: nujievik@gmail.com
"""
import sys
import os
import xml.etree.ElementTree as ET
import shutil
import re
import subprocess
import shlex
from pathlib import Path
from datetime import timedelta

AUDIO_EXTENSIONS = {'.mka', '.m4a', '.aac', '.ac3', '.dts', '.dtshd', '.eac3', '.ec3', '.flac',
                    '.mp2', '.mpa', '.mp3', '.opus', '.truehd', '.wav', '.3gp', '.flv', '.m2ts',
                    '.mkv', '.mp4', '.mpeg', '.mpg', '.mov', '.ts', '.ogg', '.ogm', '.webm'}

VIDEO_EXTENSIONS = {'.mkv', '.m4v', '.mp4', '.avi', '.h264', '.hevc', '.ts', '.3gp', '.flv',
                    '.m2ts', '.mpeg', '.mpg', '.mov', '.ogm', '.webm'}

#контейнеры которые могут содержать как видео так и аудио
CONTAINER_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.3gp', '.flv', '.m2ts', '.mpeg', '.mpg', '.mov',
                  '.ogg', '.ogm', '.ts', '.webm', '.wmv'}

SUBTITLES_EXTENSIONS = {'.ass', '.mks', '.ssa', '.sub', '.srt'}

FONT_EXTENSIONS = {'.ttf', '.otf'}

SEARCH_STRING_SUB = {'Rus sub', 'Rus. sub', 'Russian sub', 'надписи' 'sign', 'Sub'}

LIMIT_SEARCH_UPPER = 3

def execute_command(command):
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error executing the command:\n{command}\n{e.output.decode()}\nExiting the script.")
        sys.exit(1)

def get_stdout(command):
    try:
        return subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout.decode()
    except subprocess.CalledProcessError as e:
        print(f"Error executing the command:\n{command}\n{e.output.decode()}\nExiting the script.")
        sys.exit(1)

def extract_track(input_file, output, track_id):
    command = [str(mkvextract), "tracks", str(input_file), f"{track_id}:{str(output)}"]
    execute_command(command)

def extract_chapters(video, chapters):
    command = [str(mkvextract), str(video), "chapters", str(chapters)]
    execute_command(command)

def file_have_video_track(filepath):
    command = [str(mkvmerge), "-i", str(filepath)]
    return True if "video" in get_stdout(command) else False

def clear_console():
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Unix
        os.system('clear')

def delete_temp_files(directory):
    try:
        for filepath in directory.iterdir():
            if filepath.name.startswith("_temp_") and filepath.is_file():
                filepath.unlink()
    except Exception as e:
        print(f"Error: {e}")

def remove_repeat_fonts(font_set):
    stems = set()
    cleaned_set = set()
    for font in font_set:
        if not font.stem in stems:
            stems.add(font.stem)
            cleaned_set.add(font)
    return cleaned_set

def timedelta_to_str(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int(td.microseconds / 1000)
    return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds // 10:02}"  # Два знака после точки

def str_to_timedelta(time_str):
    hours, minutes, seconds = time_str.split(':')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return timedelta(seconds=total_seconds)

def write_lines_to_file(filename, *args):
    with open(filename, 'w', encoding='utf-8') as file:
        for line in args:
            file.write(f"{line}\n")

def add_lines_to_file(filename, *args):
    with open(filename, 'a', encoding='utf-8') as file:
        for line in args:
            file.write(f"{line}\n")

def read_lines_from_file(filename, num_lines):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        # Проверяем, что в файле достаточно строк
        if len(lines) >= num_lines:
            return [line.strip() for line in lines[:num_lines]]
        else:
            return None

    except FileNotFoundError:
        return None

def get_track_type_id(filepath, track_type):
    id_list = []
    pattern = r"Track ID (\d+):"
    mkvmerge_stdout = get_stdout([str(mkvmerge), "-i", str(filepath)])
    for line in mkvmerge_stdout.splitlines():
        if track_type in line:
            match = re.search(pattern, line)
            if match:
                id_list.append(int(match.group(1)))
    return id_list

def path_contain_keyword(directory, filepath):
    keywords = {"bonus", "бонус", "special", "bdmenu", "commentary", "creditless"}
    tail_path_str = str(filepath).replace(str(directory), "")
    tail_path = Path(tail_path_str)
    search_str = str(tail_path.parent).lower().replace(" ", "")

    if any(keyword in search_str for keyword in keywords):
        return True

    keywords = {"nc", "nd", "op", "pv"}
    while tail_path != tail_path.parent:
        tail_path = tail_path.parent
        search_str = tail_path.name.lower().replace(" ", "")
        if any(keyword == search_str for keyword in keywords):
            return True
    return False

def find_files_with_extensions(directory, extensions, search_name="", recursive_search=False):
    search_method = directory.rglob('*') if recursive_search else directory.glob('*')
    found_files_list = []
    for filepath in sorted(search_method):
        if recursive_search and path_contain_keyword(directory, filepath):
            continue

        filename = filepath.stem
        keywords = {"_replaced_", "_merged_", "_added_", "_temp_"}
        #если найденный файл содержит служебное имя пропускаем
        if any(keyword in filename for keyword in keywords):
            continue

        if (search_name in filename or filename in search_name) and filepath.is_file() and filepath.suffix in extensions:
            found_files_list.append(filepath)
    return found_files_list

def get_file_info(filepath, search_query):
    mkvinfo_stdout = get_stdout([str(mkvinfo), str(filepath)])
    for line in mkvinfo_stdout.splitlines():
        if search_query in line:
            if "Segment UID" in search_query:
                uid_hex = line.split(":")[-1].strip()
                # Преобразуем в строку формата 93828424aeb8a27a942fb070d17459f8
                uid_clean = "".join(byte[2:] for byte in uid_hex.split() if byte.startswith("0x"))
                return uid_clean

            if "Duration" in search_query:
                match = re.search(r"Duration:\s*(.*)", line)  # Находим всю часть после 'Duration:'
                if match:
                    file_duration = match.group(1).strip()  # Убираем пробелы
                    file_duration_timedelta = str_to_timedelta(file_duration)
                    return file_duration_timedelta

            if "Name:" in search_query:
                return True
    return None

def find_video_with_uid(search_dir, target_uid):
    video_list = find_files_with_extensions(search_dir, ".mkv")
    for video in video_list:
        video_uid = get_file_info(video, "Segment UID")
        if video_uid.lower() == target_uid.lower():
            return video
    return None

def set_output_path(video, audio_list, subtitles_list, font_set, tail=""):
    partname = f"{video.stem}{tail}"
    if audio_list:
        if save_orig_audio:
            partname = partname + "_added_audio"
        else:
            partname = partname + "_replaced_audio"

    if subtitles_list:
        if save_orig_sub:
            partname = partname + "_added_sub"
        else:
            partname = partname + "_replaced_sub"
        if font_set:
            partname = partname + "_added_font"

    output_ext = ".mkv"
    output_path = Path(save_dir) / f"{partname}{output_ext}"
    return output_path

def available_tool(tool):
    try:
        subprocess.run([str(tool), "-h"], check=True, stdout=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def set_mkvtools_paths():
    global mkvextract, mkvinfo, mkvmerge
    mkvextract = "mkvextract" if available_tool("mkvextract") else None
    mkvinfo = "mkvinfo" if available_tool("mkvinfo") else None
    mkvmerge = "mkvmerge" if available_tool("mkvmerge") else None
    if not None in [mkvextract, mkvinfo, mkvmerge]:
        return

    lmsg = "Error! MKVToolNix is not installed. Please install MKVToolNix and re-run script:\nhttps://mkvtoolnix.download/downloads.html"
    if os.name == 'nt':  # Windows
        if not mkvextract:
            mkvextract = Path(os.environ["PROGRAMFILES"]) / "MkvToolNix" / "mkvextract.exe"
            mkvextract = mkvextract if mkvextract.exists() else None
        if not mkvinfo:
            mkvinfo = Path(os.environ["PROGRAMFILES"]) / "MkvToolNix" / "mkvinfo.exe"
            mkvinfo = mkvinfo if mkvinfo.exists() else None
        if not mkvmerge:
            mkvmerge = Path(os.environ["PROGRAMFILES"]) / "MkvToolNix" / "mkvmerge.exe"
            mkvmerge = mkvmerge if mkvmerge.exists() else None
        if not None in [mkvextract, mkvinfo, mkvmerge]:
            return

        if not mkvextract:
            mkvextract = Path(os.environ["PROGRAMFILES(X86)"]) / "MkvToolNix" / "mkvextract.exe"
            mkvextract = mkvextract if mkvextract.exists() else None
        if not mkvinfo:
            mkvinfo = Path(os.environ["PROGRAMFILES(X86)"]) / "MkvToolNix" / "mkvinfo.exe"
            mkvinfo = mkvinfo if mkvinfo.exists() else None
        if not mkvmerge:
            mkvmerge = Path(os.environ["PROGRAMFILES(X86)"]) / "MkvToolNix" / "mkvmerge.exe"
            mkvmerge = mkvmerge if mkvmerge.exists() else None
        if not None in [mkvextract, mkvinfo, mkvmerge]:
            return

        if not mkvextract:
            mkvextract = Path.home() / 'Downloads' / 'mkvtoolnix' / "mkvextract.exe"
            mkvextract = mkvextract if mkvextract.exists() else None
        if not mkvinfo:
            mkvinfo = Path.home() / 'Downloads' / 'mkvtoolnix' / "mkvinfo.exe"
            mkvinfo = mkvinfo if mkvinfo.exists() else None
        if not mkvmerge:
            mkvmerge = Path.home() / 'Downloads' / 'mkvtoolnix' / "mkvmerge.exe"
            mkvmerge = mkvmerge if mkvmerge.exists() else None
        if not None in [mkvextract, mkvinfo, mkvmerge]:
            print(lmsg)
            sys.exit(1)
    else:
        print(lmsg)
        sys.exit(1)

def create_message_dictionary():
    global msg
    msg = {
        1: "[Enter] - use a default value",
        2: "DefaultAll - use default values for ALL next options"
        }
    msg[3] = f"\n{msg[1]}\n{msg[2]}\n\n"
    msg[4] = "Use a default value."
    msg[5] = f"{msg[4]}\nAll next options will be use default values."
    msg[6] = f"\n\n{msg[1]}\n{msg[2]}\nSetAll - set next generating settings for all next files\n"
    msg[7] = "Next generating settings will be set for all next files."
    msg[8] = f"Files for generating a new video not found. Checked the directory '{str(START_DIRECTORY)}', its subdirectories and {LIMIT_SEARCH_UPPER} directories up."

def user_requests():
    global pro_mode, limit_video_generating, save_dir, save_orig_audio
    clear_console()
    user_input = input(f"{msg[1]}\n\nSelect mode:\n 0 - Default mode\n 1 - PRO mode\n> ")
    clear_console()
    if user_input not in ("1", "0", ""):
        print("Incorrect input!")
    if user_input == "1":
        print("PRO mode set.")
        pro_mode = True
    else:
        print("Default mode set.")
        pro_mode = False
        return

    lmsg = "Generating will be execute for all files."
    user_input = input(f"{msg[3]}Enter the limit number of files to generate:\n> ")
    clear_console()
    if "defaultall" in user_input.lower():
        print(msg[5], lmsg)
        pro_mode = False
        return
    elif user_input == "":
        print(msg[4], lmsg)
    else:
        try:
            limit_video_generating = int(user_input)
            print(f"Generating limit has been set: {limit_video_generating}")
        except Exception:
            print("Incorrect input!", lmsg)

    lmsg = f"Save directory: {save_dir}"
    user_input = input(f"{msg[3]}Enter save directory for generating files (required full path):\n> ")
    clear_console()
    if user_input.lower() == "defaultall":
        print(msg[5], lmsg)
        pro_mode = False
        return
    elif user_input == "":
        print(msg[4], lmsg)
    else:
        try:
            path = Path(user_input)
        except Exception:
            print("Incorrect input!", msg[4], lmsg)
        if path.exists():
            save_dir = path
            print("Set save directory: ", save_dir)
        else:
            print("Path not exists!", msg[4], lmsg)

def user_requests2(video_list):
    global pro_mode, gensettings_for_all_will_be_set
    print("Found video files:")
    for video in video_list:
        print(str(video))

    lmsg = "Generate settings will be set for"
    user_input = input(f"{msg[3]}Do you want set generate settings for ALL these files? [y/n]. If not, you must be set settings for each video.\n> ")
    clear_console()
    if "defaultall" in user_input.lower():
        print(msg[5])
        pro_mode = False
        return
    elif user_input == "":
        print(msg[4], lmsg, "all files.")
        gensettings_for_all_will_be_set = True
    elif user_input.lower() in ("yes", "y"):
        print(lmsg, "all files.")
        gensettings_for_all_will_be_set = True
    elif user_input.lower() in ("no", "n"):
        print(lmsg, "each file separate.")
        gensettings_for_all_will_be_set = False
    else:
        print("Incorrect input!")
        print(lmsg, "all files.")
        gensettings_for_all_will_be_set = True

def user_requests3(video, audio_list, subtitles_list, font_set):
    global pro_mode, gensettings_for_all_will_be_set, gensettings_for_all_setted, save_orig_audio, save_orig_sub, save_orig_font
    output_str = f"Processed files:\nVideo: \n{str(video)}"
    if audio_list:
        output_str = output_str + "\nAudio: \n" + "\n".join([str(audio) for audio in audio_list])
    if subtitles_list:
        output_str = output_str + "\nSubtitle: \n" + "\n".join([str(sub) for sub in subtitles_list])
        if font_set:
            output_str = output_str + "\nFont: \n" + "\n".join([str(font) for font in font_set])

    lmsg = msg[3] if gensettings_for_all_will_be_set else msg[6]

    lmsg2 = "Do you want to save original audio? [y/n].\n> "
    clear_console()
    print(output_str, lmsg)
    user_input = input(lmsg2)
    clear_console()
    if "setall" in user_input.lower():
        gensettings_for_all_will_be_set = True
        lmsg = msg[3]
        clear_console()
        print(msg[7], output_str, lmsg)
        user_input = input(lmsg2)
    if "defaultall" in user_input.lower():
        print(msg[5])
        save_orig_audio = not audio_dir_found or not audio_list
        pro_mode = False
        return
    elif user_input == "":
        print(msg[4])
        save_orig_audio = not audio_dir_found or not audio_list
    elif user_input.lower() in ("yes", "y"):
        print("Original audio will be save.")
        save_orig_audio = True
    elif user_input.lower() in ("no", "n"):
        print("Original audio will NOT be save.")
        save_orig_audio = False
    else:
        print("Incorrect input!", msg[4])
        save_orig_audio = not audio_dir_found or not audio_list

    lmsg2 = "Do you want to save original subtitles? [y/n].\n> "
    print(f"\n{output_str}", lmsg)
    user_input = input(lmsg2)
    clear_console()
    if "setall" in user_input.lower():
        gensettings_for_all_will_be_set = True
        lmsg = msg[3]
        clear_console()
        print(msg[7], output_str, lmsg)
        user_input = input(lmsg2)
    if "defaultall" in user_input.lower():
        print(msg[5])
        save_orig_sub = not subtitles_dir_found or not subtitles_list
        pro_mode = False
        return
    elif user_input == "":
        print(msg[4])
        save_orig_sub = not subtitles_dir_found or not subtitles_list
    elif user_input.lower() in ("yes", "y"):
        print("Original subtitles will be save.")
        save_orig_sub = True
    elif user_input.lower() in ("no", "n"):
        print("Original subtitles will NOT be save.")
        save_orig_sub = False
    else:
        print("Incorrect input!", msg[4])
        save_orig_sub = not subtitles_dir_found or not subtitles_list

    if save_orig_sub:
        save_orig_font = True
    elif not save_orig_sub and subtitles_list:
        lmsg = "Do you want to save original font? External subtitles also will be used original font. \n[y/n]\n> "
        print(f"\n{output_str}", lmsg)
        user_input = input(lmsg2)
        clear_console()
        if "setall" in user_input.lower():
            gensettings_for_all_will_be_set = True
            lmsg = msg[3]
            clear_console()
            print(msg[7], output_str, lmsg)
            user_input = input(lmsg2)
        if "defaultall" in user_input.lower():
            print(msg[5])
            save_orig_font = True
            pro_mode = False
            return
        elif user_input == "":
            print(msg[4])
            save_orig_font = True
        elif user_input.lower() in ("yes", "y"):
            print("Original font will be save.")
            save_orig_font = True
        elif user_input.lower() in ("no", "n"):
            print("Original font will NOT be save.")
            save_orig_font = False
        else:
            print("Incorrect input!", msg[4])
            save_orig_font = True

    elif not save_orig_sub and not subtitles_list:
        save_orig_font = False

    if gensettings_for_all_will_be_set:
        gensettings_for_all_setted = True

def find_subdirectorys_by_string(base_dir):
    search_method = base_dir.glob('*')
    found_dirs_list = []
    repeat_search = True
    while repeat_search:
        repeat_search = False
        for subdir in sorted(search_method):
            if subdir.is_dir() and any(keyword.lower() in subdir.name.lower() for keyword in SEARCH_STRING_SUB):
                found_dir = subdir
                found_dirs_list.append(found_dir)
                search_method = found_dir.rglob('*')
                repeat_search = True
    return found_dirs_list

def merge_file_segments(segment_list, output):
    command = [str(mkvmerge), "-o", str(output)]
    command.append(segment_list[0])
    for segment in segment_list[1:]:
        command.append(f"+{str(segment)}")
    execute_command(command)

def search_video_dir_upper(directory, extensions):
    filepath_list = find_files_with_extensions(directory, extensions)
    for filepath in filepath_list:
        count = 0
        search_dir = directory
        while count <= LIMIT_SEARCH_UPPER:
            video_list = find_files_with_extensions(search_dir, VIDEO_EXTENSIONS, filepath.stem)
            for video in video_list:
                #не выполняем если видео совпадает с файлом
                if video == filepath:
                    continue
                #проверяем что в видео есть видеодорожка, если нужно
                if video.suffix not in CONTAINER_EXTENSIONS or video.parent != directory or file_have_video_track(video):
                    video_dir = video.parent
                    return True, video_dir
            search_dir = search_dir.parent
            count += 1
    return False, None

def find_dir_with_filename_to_videoname(video_list, search_dir, search_extensions, recursive_search):
    new_found_list = []
    for video in video_list:
        found_list = find_files_with_extensions(search_dir, search_extensions, video.stem, recursive_search)
        for found in found_list:
            #если найденный файл == видео пропускаем
            if found == video:
                continue
            #проверяем что в видео есть видеодорожка, если нужно
            if video.suffix not in CONTAINER_EXTENSIONS or video.parent != search_dir or file_have_video_track(video):
                return found.parent
    return None

def search_subdir_when_adir_start_dir(audio_dir, video_dir):
    recursive_search = False
    video_list = find_files_with_extensions(video_dir, VIDEO_EXTENSIONS)
    if video_dir == audio_dir:
        subtitles_dir = find_dir_with_filename_to_videoname(video_list, audio_dir, SUBTITLES_EXTENSIONS, recursive_search)
        if subtitles_dir:
            return True, subtitles_dir
        else:
            return False, None

    search_dir_list = [audio_dir, video_dir]
    #поиск в стартовой директории и в видеодир без рекурсии
    for search_dir in search_dir_list:
        subtitles_dir = find_dir_with_filename_to_videoname(video_list, search_dir, SUBTITLES_EXTENSIONS, recursive_search)
        if subtitles_dir:
            return True, subtitles_dir

    #поиск в сабдиректориях по запросу с рекурсией
    search_dir_list = [video_dir] + find_subdirectorys_by_string(video_dir)
    for search_dir in reversed(search_dir_list):
        for recursive_search in [False, True]:
            subtitles_dir = find_dir_with_filename_to_videoname(video_list, search_dir, SUBTITLES_EXTENSIONS, recursive_search=recursive_search)
            if subtitles_dir:
                return True, subtitles_dir

    return False, None

def get_trackname_from_tail(tail):
    execute = True
    while execute:
        if re.match(r'^\..{3}\..*$', tail):
            tail = tail[4:]
        else:
            execute = False

    for ext in AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | SUBTITLES_EXTENSIONS:
        if tail.lower().startswith(ext):
            tail = tail[len(ext):]
        if tail.lower().endswith(ext):
            tail = tail[:-len(ext)]

    tail = tail.strip(' _.')
    if tail.startswith('[') and tail.endswith(']') and tail.count('[') == 1:
        tail = tail.strip('[]')
    return tail

def get_trackname_from_dirname(name):
    if name.startswith('[') and name.endswith(']') and name.count('[') == 1:
        name = name.strip(' _.[]')
    else:
        name = name.strip(' _.')
    return name

def get_trackname(tail, dir_name):
    tail = get_trackname_from_tail(tail) if len(tail) > 2 else tail
    if len(tail) > 2:
        trackname = tail
    else:
        trackname = get_trackname_from_dirname(dir_name)
    return trackname

def clear_lists_create_dictionarys(video_list, audio_list, subtitles_list):
    new_video_list = []
    audio_dictionary = {}
    audio_trackname_dictionary = {}
    subtitles_dictionary = {}
    sub_trackname_dictionary = {}

    count = 0
    for video in video_list:
        skip_video = False
        save_video = False
        found_video_track = False
        audio_dictionary[f"audio_list_{count}"] = []
        audio_trackname_dictionary[f"audio_trackname_list_{count}"] = []
        subtitles_dictionary[f"subtitles_list_{count}"] = []
        sub_trackname_dictionary[f"subtitles_trackname_list_{count}"] = []

        for audio in audio_list:
            #если audio совпадает с video пропускаем audio или video
            if video == audio:
                if found_video_track or file_have_video_track(video):
                    found_video_track = True
                    continue
                else:
                    skip_video = True
                    break

            if video.stem in audio.stem:
                audio_dictionary[f"audio_list_{count}"].append(audio)
                tail = audio.stem[len(video.stem):]
                dir_name = audio.parent.name
                trackname = get_trackname(tail, dir_name)
                audio_trackname_dictionary[f"audio_trackname_list_{count}"].append(trackname)
                save_video = True

        if skip_video:
            continue

        for subtitles in subtitles_list:
            #если имена частично совпадают
            if video.stem in subtitles.stem:
                subtitles_dictionary[f"subtitles_list_{count}"].append(subtitles)
                tail = subtitles.stem[len(video.stem):]
                dir_name = subtitles.parent.name
                trackname = get_trackname(tail, dir_name)
                sub_trackname_dictionary[f"subtitles_trackname_list_{count}"].append(trackname)
                save_video = True

        if save_video:
            new_video_list.append(video)
            count += 1

    return new_video_list, audio_dictionary, audio_trackname_dictionary, subtitles_dictionary, sub_trackname_dictionary

def get_file_list_dictionarys():
    global audio_dir_found, subtitles_dir_found
    search_dir = START_DIRECTORY
    audio_dir_found = False
    subtitles_dir_found = False
    font_dir_found = False

    #пробуем найти видеодир в директориях выше
    #через аудио
    video_dir_found, video_dir = search_video_dir_upper(search_dir, AUDIO_EXTENSIONS)
    if video_dir_found:
        audio_dir = search_dir
        audio_dir_found = True
        subtitles_dir_found, subtitles_dir = search_subdir_when_adir_start_dir(audio_dir, video_dir)
    #через сабы
    if not video_dir_found:
        video_dir_found, video_dir = search_video_dir_upper(search_dir, SUBTITLES_EXTENSIONS)
        if video_dir_found:
            subtitles_dir = search_dir
            subtitles_dir_found = True

    #если найден сабдир ищем фонтдир
    if subtitles_dir_found:
        font_list = find_files_with_extensions(subtitles_dir, FONT_EXTENSIONS, "", recursive_search=True)
        if font_list:
            font_dir = font_list[0].parent
            font_dir_found = True
        else: #пробуем поискать в директории выше
            if subtitles_dir != video_dir:
                font_list = find_files_with_extensions(subtitles_dir.parent, FONT_EXTENSIONS, "", recursive_search=True)
        if not font_dir_found and font_list:
            font_dir = font_list[0].parent
            font_dir_found = True

    #формируем списки файлов
    audio_list = []
    subtitles_list = []
    font_set = set()

    search_dir = video_dir if video_dir_found else START_DIRECTORY
    video_list = find_files_with_extensions(search_dir, VIDEO_EXTENSIONS)
    if not video_list:
        print(msg[8])
        sys.exit(0)

    if audio_dir_found or subtitles_dir_found:
        recursive_search = False
        if audio_dir_found:
            search_dir = audio_dir
            audio_list = find_files_with_extensions(search_dir, AUDIO_EXTENSIONS, "", recursive_search)
        if subtitles_dir_found:
            search_dir = subtitles_dir
            subtitles_list = find_files_with_extensions(search_dir, SUBTITLES_EXTENSIONS, "", recursive_search)
        if font_dir_found:
            search_dir = font_dir
            font_set = set(find_files_with_extensions(search_dir, FONT_EXTENSIONS, "", recursive_search))

    else:
        search_dir = START_DIRECTORY
        recursive_search = True

        audio_list = find_files_with_extensions(search_dir, AUDIO_EXTENSIONS, "", recursive_search)
        subtitles_list = find_files_with_extensions(search_dir, SUBTITLES_EXTENSIONS, "", recursive_search)
        font_set = set(find_files_with_extensions(search_dir, FONT_EXTENSIONS, "", recursive_search))
        if font_set:
            font_set = remove_repeat_fonts(font_set)

    video_list, audio_dictionary, audio_trackname_dictionary, subtitles_dictionary, sub_trackname_dictionary = clear_lists_create_dictionarys(video_list, audio_list, subtitles_list)
    if not video_list: #пробуем найти mkv мб линкованное
        video_list = find_files_with_extensions(search_dir, ".mkv")
        if not video_list:
            print(msg[8])
            sys.exit(0)
        else:
            video_list = [video for video in video_list if file_have_video_track(video)]
            audio_dictionary = audio_trackname_dictionary = subtitles_dictionary = sub_trackname_dictionary = font_set = {}
            if not video_list:
                print(msg[8])
                sys.exit(0)

    return video_list, audio_dictionary, audio_trackname_dictionary, subtitles_dictionary, sub_trackname_dictionary, font_set

def get_chapters_info(video, chapters_file):
    try:
        tree = ET.parse(chapters_file)
    except Exception:
        return [], [], []
    root = tree.getroot()
    chapter_uid_list = []
    chapter_start_list = []
    chapter_end_list = []

    for chapter_atom in root.findall(".//ChapterAtom"):
        chapter_uid = chapter_atom.find("ChapterSegmentUID")
        chapter_uid = chapter_uid.text if chapter_uid is not None else None
        chapter_uid_list.append(chapter_uid)

        chapter_start = chapter_atom.find("ChapterTimeStart")
        chapter_start = str_to_timedelta(chapter_start.text) if chapter_start is not None else None
        chapter_start_list.append(chapter_start)

        chapter_end = chapter_atom.find("ChapterTimeEnd")
        chapter_end = str_to_timedelta(chapter_end.text) if chapter_end is not None else None
        chapter_end_list.append(chapter_end)

    if all(uid is None for uid in chapter_uid_list): #если нет внешних файлов
        return [], [], []

    if None in chapter_start_list or None in chapter_end_list:
        temp_start_list = []
        temp_end_list = []
        prev_nonid_end = timedelta(0)
        length = len(chapter_start_list)
        count = 0
        for start in chapter_start_list:
            end = chapter_end_list[count]
            uid = chapter_uid_list[count]

            if start:
                temp_start = start
            else:
                if uid:
                    temp_start = timedelta(0)
                else:
                    temp_start = prev_nonid_end

            if end:
                temp_end = end
            else:
                if length > count+1 and chapter_start_list[count+1]:
                    temp_end = chapter_start_list[count+1]

                else:
                    if uid:
                        temp_video = find_video_with_uid(video.parent, uid)
                        if not temp_video:
                            print(f"Video file with uid {uid} not found in the video directory '{str(video.parent)}'\nThis file is part of the linked video '{str(video)}' and is required for merging. Please move this file to the video directory and re-run the script.")
                            sys.exit(1)
                    else:
                        temp_video = video
                    temp_end = get_file_info(temp_video, "Duration")

            temp_start_list.append(temp_start)
            temp_end_list.append(temp_end)
            if not uid:
                prev_nonid_end = temp_end
            count += 1
        chapter_start_list = temp_start_list
        chapter_end_list = temp_end_list

    return chapter_uid_list, chapter_start_list, chapter_end_list

def rw_uid_file_info(video_dir, uid, start, end, execute_split):
    txt_uid = Path(save_dir) / f"_temp_{uid}.txt"
    segment = None
    length = None
    offset_start = None
    offset_end = None
    read = read_lines_from_file(txt_uid, 6)
    if read:
        line1, line2, line3, line4, line5, line6 = read
        to_split = Path(line1)
        #если время предыдущего сплита совпадает
        if str_to_timedelta(line2) == start and (str_to_timedelta(line3) == end or str_to_timedelta(line4) <= end):
            #и нужный сплит существует не сплитуем
            segment = Path (save_dir) / f"_temp_{uid}.mkv"
            if segment.exists():
                length = str_to_timedelta(line4)
                offset_start = str_to_timedelta(line5)
                offset_end = str_to_timedelta(line6)
                execute_split = False
    else:
        to_split = find_video_with_uid(video_dir, uid)
        write_lines_to_file(txt_uid, to_split, start, end)

    return to_split, segment, length, offset_start, offset_end, txt_uid, execute_split

def get_segment_info(mkvmerge_stdout, partname, split_start, split_end):
    #ищем переназначения
    timestamps = re.findall(r'Timestamp used in split decision: (\d{2}:\d{2}:\d{2}\.\d{9})', mkvmerge_stdout)
    if len(timestamps) == 2:
        segment = Path(partname.parent) / f"{partname.stem}-002{partname.suffix}"
        defacto_start = str_to_timedelta(timestamps[0])
        defacto_end = str_to_timedelta(timestamps[1])
        offset_start = defacto_start - split_start
        offset_end = defacto_end - split_end
    elif len(timestamps) == 1:
        timestamp = str_to_timedelta(timestamps[0])
        #если переназначение для старта
        if split_start > timedelta(0):
            segment = Path(partname.parent) / f"{partname.stem}-002{partname.suffix}"
            defacto_start = timestamp
            defacto_end = defacto_start + get_file_info(segment, "Duration")
            offset_start = defacto_start - split_start
            offset_end = timedelta(0) #время указанное для сплита выходит за границы файла; реально воспроизводится только то что в границах файла
        else:
            segment = Path(partname.parent) / f"{partname.stem}-001{partname.suffix}"
            defacto_start = timedelta(0)
            defacto_end = timestamp
            offset_start = timedelta(0)
            offset_end = defacto_end - split_end
    else:
        segment = Path(partname.parent) / f"{partname.stem}-001{partname.suffix}"
        defacto_start = timedelta(0)
        defacto_end = get_file_info(segment, "Duration")
        offset_start = timedelta(0)
        offset_end = timedelta(0)

    return segment, defacto_start, defacto_end, offset_start, offset_end

def split_file(input_file, partname, start, end, file_type="video"):
    command = [str(mkvmerge), "-o", str(partname), "--split", f"timecodes:{start},{end}", "--no-global-tags", "--no-chapters", "--no-subtitles"]
    if "video" in file_type:
        command.append("--no-audio")
        if not save_orig_font:
            command.append("--no-attachments")
    else:
        command.extend(["--no-video", "--no-attachments"])
    command.append(str(input_file))

    # Выполняем команду и ищем переназначения
    mkvmerge_stdout = get_stdout(command)
    segment, defacto_start, defacto_end, offset_start, offset_end = get_segment_info(mkvmerge_stdout, partname, start, end)
    length = defacto_end - defacto_start

    return segment, length, offset_start, offset_end

def get_segment_linked_video(video, uid, start, end, prev_nonuid_end, count, lengths, prev_offset_end):
    execute_split = True
    video_dir = video.parent
    chapter_start = start
    chapter_end = end
    partname = Path (save_dir) / f"_temp_{count}.mkv"

    if uid:
        to_split, segment, length, offset_start, offset_end, txt_uid, execute_split = rw_uid_file_info(video_dir, uid, start, end, execute_split)
    else:
        to_split = video
        start = prev_nonuid_end

    if execute_split:
        prev_lengths = lengths
        segment, length, offset_start, offset_end = split_file(to_split, partname, start, end)
        lengths = lengths + length

        if uid: # сплит по внешнему файлу переименовываем чтоб использовать дальше
            new_path = Path (save_dir) / f"_temp_{uid}.mkv"
            if new_path.exists():
                new_path.unlink()
            segment.rename(new_path)
            segment = new_path
            add_lines_to_file(txt_uid, lengths - prev_lengths, offset_start, offset_end)
    else:
        lengths = lengths + length

    if uid:
        offset_start = prev_offset_end + offset_start
        offset_end = prev_offset_end + offset_end
    else:
        offset_start = (start - chapter_start) + offset_start
        offset_end = offset_end
        prev_nonuid_end = chapter_end + offset_end

    return to_split, segment, offset_start, offset_end, lengths, prev_nonuid_end

def get_all_segments_linked_video(video, uid_list, start_list, end_list):
    source_list = []
    segment_list = []
    offset_start_list = []
    offset_end_list = []
    lengths_list = []
    lengths = timedelta(0)
    offset_start = timedelta(0)
    offset_end = timedelta(0)
    prev_nonuid_end = timedelta(0)

    count = 0
    for uid in uid_list:
        start = start_list[count]
        end = end_list[count]

        source, segment, offset_start, offset_end, lengths, prev_nonuid_end = get_segment_linked_video(video, uid, start, end, prev_nonuid_end, count, lengths, offset_end)
        source_list.append(source)
        segment_list.append(segment)
        offset_start_list.append(offset_start)
        offset_end_list.append(offset_end)
        lengths_list.append(lengths)
        count += 1
    return source_list, segment_list, offset_start_list, offset_end_list, lengths_list

def get_retimed_segments_orig_audio(video, source_list, lengths_list):
    a_segment_list = []
    prev_lengths = timedelta(0)
    uid_lenghs = timedelta(0)
    a_lengths = timedelta(0)
    count = 0
    for source in source_list:
        lengths = lengths_list[count]
        length = lengths - prev_lengths
        offset_lengths = a_lengths - prev_lengths

        if source == video:
            start = prev_lengths - uid_lenghs - offset_lengths if count > 0 else timedelta(0)
            end = start + length
        else:
            start = timedelta(0)
            end = start + length
            uid_lenghs = uid_lenghs + length

        partname = Path(save_dir) / f"_temp_{count}.mka"
        a_segment, a_length, offset_start, offset_end = split_file(source, partname, start, end, "audio")
        if offset_start > timedelta(milliseconds=200) or offset_end > timedelta(milliseconds=200):
            new_start = start - offset_start if start - offset_start > timedelta(0) else start
            new_end = end - offset_end
            a_segment, a_length, offset_start, offset_end = split_file(source, partname, new_start, new_end, "audio")
        a_lengths = a_lengths + a_length
        a_segment_list.append(a_segment)
        prev_lengths = lengths
        count += 1
    return a_segment_list

def get_retimed_segments_ext_audio(audio, video, source_list, lengths_list, offset_start_list, offset_end_list):
    count = 0
    start = timedelta(0)
    end = timedelta(0)
    prev_lengths = timedelta(0)
    a_lengths = timedelta(0)
    retimed_segment_ext_audio_list = []
    for lengths in lengths_list:
        add_compensation = False
        length = lengths - prev_lengths
        offset_start = offset_start_list[count]
        offset_end = offset_end_list[count]
        offset_audio_to_video = a_lengths - prev_lengths

        if source_list[count] == video:
            start = prev_lengths + offset_audio_to_video

            if offset_end > timedelta(milliseconds=2000) and len(source_list) > count+2 and video == source_list[count+2]:
                end = lengths - offset_end
                compensation_start = lengths_list[count+1] - offset_start_list[count+2]
                add_compensation = True
            else:
                end = lengths
        else:
            start = prev_lengths - offset_start + offset_audio_to_video
            end = start + length

        partname = Path(save_dir) / f"_temp_{count}.mka"
        a_segment, a_length, split_offset_start, split_offset_end = split_file(audio, partname, start, end, "audio")
        if split_offset_start > timedelta(milliseconds=200) or split_offset_end > timedelta(milliseconds=200):
            new_start = start - split_offset_start if start - split_offset_start > timedelta(0) else start
            new_end = end - split_offset_end
            a_segment, a_length, *_ = split_file(audio, partname, new_start, new_end, "audio")
        if add_compensation:
            compensation_length = length - a_length
            if compensation_length > timedelta(milliseconds=500):
                partname = Path(save_dir) / f"_temp_compensation_{count}.mka"
                compensation_end = compensation_start + compensation_length
                compensation_segment, compensation_length, *_ = split_file(audio, partname, compensation_start, compensation_end, "audio")
            add_compensation = True if compensation_length > timedelta(milliseconds=500) else False

        if add_compensation:
            retimed_segment_ext_audio_list.extend([a_segment, compensation_segment])
            a_lengths = a_lengths + a_length + compensation_length
        else:
            retimed_segment_ext_audio_list.append(a_segment)
            a_lengths = a_lengths + a_length
        prev_lengths = lengths
        count += 1
    return retimed_segment_ext_audio_list

def get_retimed_audio_list(audio_list, video, source_list, lengths_list, offset_start_list, offset_end_list):
    count = 0
    count_insert = 0
    retimed_audio_list = []
    if save_orig_audio:
        orig_audio = Path(save_dir) / f"_temp_audio_{count}.mka"
        segment_list = get_retimed_segments_orig_audio(video, source_list, lengths_list)
        merge_file_segments(segment_list, orig_audio)
        #проверяем сколько аудио дорожек внутри
        audio_id_list = get_track_type_id(orig_audio, "audio")
        amount_tracks = len(audio_id_list)
        if amount_tracks > 1:
            new_path =  Path(save_dir) / f"_temp_audio_{count+amount_tracks+1}.mka"
            if new_path.exists():
                new_path.unlink()
            orig_audio.rename(new_path)

            for audio_id in audio_id_list:
                retimed_audio = Path(save_dir) / f"_temp_audio_{count}.mka"
                extract_track(new_path, retimed_audio, audio_id)
                retimed_audio_list.append(retimed_audio)
                count += 1
                count_insert += 1
        else:
            retimed_audio_list.append(orig_audio)
            count += 1
            count_insert += 1

    for audio in audio_list:
        retimed_audio = Path(save_dir) / f"_temp_audio_{count}.mka"
        segment_list = get_retimed_segments_ext_audio(audio, video, source_list, lengths_list, offset_start_list, offset_end_list)
        merge_file_segments(segment_list, retimed_audio)
        retimed_audio_list.append(retimed_audio)
        count += 1
    return retimed_audio_list, count_insert

def retime_original_sub(segment_orig_sub_list, video, source_list, lengths_list, offset_start_list, offset_end_list):
    count = 0
    dictionary = {}
    #считываем все сабы
    for sub in segment_orig_sub_list:
        with open(sub, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            dictionary[f"lines{count}"] = lines
            count += 1
    total_lines = list(dictionary.values())

    retimed_sub = segment_orig_sub_list[0]
    with open(retimed_sub, 'w', encoding='utf-8') as file:
        for line in total_lines[0]:
            if not line.startswith("Dialogue:"):
                file.write(line) #записываем строки до диалогов
            else:
                break

        #ретаймим
        count = 0
        prev_lengths = timedelta(0)
        prev_offset_end = timedelta(0)
        lengths_ext_files = timedelta(0)
        prev_nonuid_offset_end = timedelta(0)
        for lengths in lengths_list:
            length = lengths - prev_lengths
            offset_start = offset_start_list[count]
            offset_end = offset_end_list[count]

            if source_list[count] == video:
                start = prev_lengths - lengths_ext_files
                retime_offset = (offset_start - prev_nonuid_offset_end) + lengths_ext_files
                remove_border_start = start
            else:
                start = offset_start - prev_offset_end if offset_start - prev_offset_end > timedelta(0) else timedelta(0)
                retime_offset = start + prev_lengths
                remove_border_start = start - offset_start if start - offset_start > timedelta(0) else start
            remove_border_end = remove_border_start + length

            for line in dictionary[f"lines{count}"]:
                if line.startswith("Dialogue:"):
                    # Извлекаем временные метки
                    parts = line.split(',')
                    str_dialogue_time_start = parts[1].strip()
                    str_dialogue_time_end = parts[2].strip()
                    dialogue_time_start = str_to_timedelta(str_dialogue_time_start)
                    dialogue_time_end = str_to_timedelta(str_dialogue_time_end)

                    #не включаем строки не входящие в сегмент
                    if dialogue_time_start < remove_border_start and dialogue_time_end < remove_border_start:
                        continue
                    elif dialogue_time_start > remove_border_end and dialogue_time_end > remove_border_end:
                        continue
                    else: #ретаймим и записываем
                        new_dialogue_time_start = dialogue_time_start + retime_offset
                        new_dialogue_time_end = dialogue_time_end + retime_offset
                        str_new_dialogue_time_start = timedelta_to_str(new_dialogue_time_start)
                        str_new_dialogue_time_end = timedelta_to_str(new_dialogue_time_end)
                        line = f"{parts[0]},{str_new_dialogue_time_start},{str_new_dialogue_time_end},{','.join(parts[3:])}"
                        file.write(line)
            prev_lengths = lengths
            prev_offset_end = offset_end
            if source_list[count] == video:
                prev_nonuid_offset_end = offset_end
            else:
                lengths_ext_files = lengths_ext_files + length
            count += 1
    return retimed_sub

def retime_external_sub(input_sub, video, source_list, lengths_list, offset_start_list, offset_end_list):
    with open(input_sub, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    retimed_sub = input_sub
    with open(retimed_sub, 'w', encoding='utf-8') as file:
        for line in lines:
            if not line.startswith("Dialogue:"):
                file.write(line) #записываем строки до диалогов
            else:
                break

        prev_lengths = timedelta(0)
        prev_offset_end = timedelta(0)
        count = 0
        for lengths in lengths_list:
            length = lengths - prev_lengths
            offset_start = offset_start_list[count]
            offset_end = offset_end_list[count]

            start = prev_lengths
            end = lengths
            if video == source_list[count]: #если отрезок из основного файла
                retime_offset = offset_start - prev_offset_end
                remove_border_start = start - retime_offset
                remove_border_end = remove_border_start + length - offset_end
            else:
                retime_offset = offset_start
                remove_border_start = start
                remove_border_end = remove_border_start + length - offset_end

            for line in lines:
                if line.startswith("Dialogue:"):
                    # Извлекаем временные метки
                    parts = line.split(',')
                    str_dialogue_time_start = parts[1].strip()
                    str_dialogue_time_end = parts[2].strip()
                    dialogue_time_start = str_to_timedelta(str_dialogue_time_start)
                    dialogue_time_end = str_to_timedelta(str_dialogue_time_end)

                    #не включаем строки не входящие в сегмент
                    if dialogue_time_start < remove_border_start and dialogue_time_end < remove_border_start:
                        continue
                    elif dialogue_time_start > remove_border_end and dialogue_time_end > remove_border_end:
                        continue
                    else: #ретаймим и записываем
                        new_dialogue_time_start = dialogue_time_start + retime_offset
                        new_dialogue_time_end = dialogue_time_end + retime_offset
                        str_new_dialogue_time_start = timedelta_to_str(new_dialogue_time_start)
                        str_new_dialogue_time_end = timedelta_to_str(new_dialogue_time_end)
                        line = f"{parts[0]},{str_new_dialogue_time_start},{str_new_dialogue_time_end},{','.join(parts[3:])}"
                        file.write(line)
            prev_lengths = lengths
            prev_offset_end = offset_end
            count += 1
    return retimed_sub

def get_retimed_sub_list(ext_subtitles_list, video, source_list, lengths_list, offset_start_list, offset_end_list):
    count = 0
    count_insert = 0
    retimed_sub_list = []
    segment_orig_sub_list = []
    #проверяем сколько дорожек субтитров в исходном видео
    subtitles_id_list = get_track_type_id(video, "subtitles")
    for subtitles_id in subtitles_id_list:
        count_temp = 0
        for source in source_list:
            split_original_sub = Path(save_dir) / f"_temp_subtitles_{count + count_temp}.ass"
            extract_track(source, split_original_sub, subtitles_id)
            segment_orig_sub_list.append(split_original_sub)
            count_temp += 1
        #объединяем и ретаймим
        retimed_original_sub = retime_original_sub(segment_orig_sub_list, video, source_list, lengths_list, offset_start_list, offset_end_list)
        retimed_sub_list.append(retimed_original_sub)
        count += 1
        count_insert += 1

    for subtitles in ext_subtitles_list:
        sub_for_retime = Path(save_dir) / f"_temp_subtitles_{count}.ass"
        if subtitles.suffix != ".ass":
            print(f"Skip subtitles! {str(subtitles)} \nThese subtitles need to be retimed because the video file has segment linking. Retime is only possible for .ass subtitles.")
            continue
        else:
            shutil.copy(subtitles, sub_for_retime)
        retimed_external_sub = retime_external_sub(sub_for_retime, video, source_list, lengths_list, offset_start_list, offset_end_list)
        retimed_sub_list.append(retimed_external_sub)
        count += 1
    return retimed_sub_list, count_insert

def processing_linked_video(video, audio_list, subtitles_list, font_set):
    chapters = Path(save_dir) / "_temp_chapters.xml"
    if chapters.exists():
        chapters.unlink()
    extract_chapters(video, chapters)
    if not chapters.exists():
        return None

    chapter_uid_list, chapter_start_list, chapter_end_list = get_chapters_info(video, chapters)
    if not chapter_uid_list:
        return None
    else:
        output = set_output_path(video, audio_list, subtitles_list, font_set, "_merged_video")
        if output.exists():
            return output, None, None, None, None, None

    source_list, segment_video_list, offset_start_list, offset_end_list, lengths_list = get_all_segments_linked_video(video, chapter_uid_list, chapter_start_list, chapter_end_list)

    retimed_audio_list = []
    count_insert_audio = 0
    if save_orig_audio or audio_list:
        retimed_audio_list, count_insert_audio = get_retimed_audio_list(audio_list, video, source_list, lengths_list, offset_start_list, offset_end_list)

    retimed_sub_list = []
    count_insert_sub = 0
    if save_orig_sub or subtitles_list:
        retimed_sub_list, count_insert_sub = get_retimed_sub_list(subtitles_list, video, source_list, lengths_list, offset_start_list, offset_end_list)

    return output, segment_video_list, retimed_audio_list, retimed_sub_list, count_insert_audio, count_insert_sub

def merge_all_files(output, video_list, audio_list, audio_trackname_list, subtitles_list, subtitles_trackname_list, font_set, save_chapters=True):
    command = [str(mkvmerge), "-o", str(output)]
    if not save_chapters:
        command.append("--no-chapters")
    if not save_orig_audio:
        command.append("--no-audio")
    if not save_orig_sub:
        command.append("--no-subtitles")
    if not save_orig_font:
        command.append("--no-attachments")

    #добавляем видеофайлы
    command.append(str(video_list[0]))
    for video in video_list[1:]:
        command.append(f"+{str(video)}")

    #Добавляем аудио
    count = 0
    for audio in audio_list:
        track_name = audio_trackname_list[count]
        if track_name and not (audio.suffix in (".mka", ".mkv") and get_file_info(audio, "Name:")):
            track_id_list = get_track_type_id(audio, "audio") #получаем инфу об аудиотреках
            for track_id in track_id_list:
                command.extend(["--track-name", f"{track_id}:{track_name}", str(audio)])
        else:
            command.append(str(audio))
        count += 1

    #сабы
    count = 0
    for sub in subtitles_list:
        track_name = subtitles_trackname_list[count]
        if track_name and not (sub.suffix in (".mks", ".mkv") and get_file_info(sub, "Name:")):
            track_id_list = get_track_type_id(sub, "subtitles")
            for track_id in track_id_list:
                command.extend(["--track-name", f"{track_id}:{track_name}", str(sub)])
        else:
            command.append(str(sub))
        count += 1
    #добавляем фонты если добавлены сабы
    if count > 0:
        for font in font_set:
            command.extend(["--attach-file", str(font)])
    print(f"\nGenerating a merged video file using mkvmerge. Executing the command: \n{command}")
    
    lmsg = f"The command was executed successfully. The generated video file was saved to:\n{str(output)}"
    try:
        command_out = subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout.decode()
        if pro_mode:
            print(command_out)
        print(lmsg)

    except subprocess.CalledProcessError as e:
        command_out = e.output.decode()
        cleaned_out = ''.join(command_out.split()).lower()
        last_line_out = command_out.splitlines()[-1]
        cleaned_lline_out = ''.join(last_line_out.split()).lower()
        if pro_mode:
            print(command_out)

        if not cleaned_lline_out.startswith("error"):
            print(lmsg)
        
            if "thecodec'sprivatedatadoesnotmatch" in cleaned_out:
                print(f"Attention! The video file maybe corrupted because video parts have mismatched codec parameters. Please check the video file.")

        else:
            if "containschapterswhoseformatwasnotrecognized" in cleaned_lline_out:
                print(f"{last_line_out}\nTrying to generate without chapters.")
                merge_all_files(output, video_list, audio_list, audio_trackname_list, subtitles_list, subtitles_trackname_list, font_set, save_chapters=False)
        
            elif "nospaceleft" in cleaned_lline_out:
                if output.exists():
                    output.unlink()
                delete_temp_files(save_dir)
                print(f"Error writing file!\nPlease re-run the script with a different save directory.\nExiting the script.")
                sys.exit(1)

            else:
                delete_temp_files(save_dir)
                print(f"Error executing the command!\n{last_line_out}\nExiting the script.")
                sys.exit(1)

def set_flags_call_merge(video_list, audio_dictionary, audio_trackname_dictionary, subtitles_dictionary, sub_trackname_dictionary, font_set):
    global limit_video_generating, save_orig_audio, save_orig_sub, save_orig_font
    if pro_mode:
        user_requests2(video_list)
    initial_font_set = font_set
    count = 0
    generated_count = 0
    gen_before_count = 0
    for video in video_list:
        video_to_merge_list = [video]
        font_list = initial_font_set

        audio_list = audio_dictionary.get(f"audio_list_{count}", [])
        audio_trackname_list = audio_trackname_dictionary.get(f"audio_trackname_list_{count}", [])
        if not pro_mode:
            save_orig_audio = not audio_dir_found or not audio_list

        subtitles_list = subtitles_dictionary.get(f"subtitles_list_{count}", [])
        subtitles_trackname_list = sub_trackname_dictionary.get(f"subtitles_trackname_list_{count}", [])
        if not pro_mode:
            save_orig_font = True #вшитые фонты могут юзать как вшитые сабы так и внешние
            save_orig_sub = not subtitles_dir_found or not subtitles_list
            font_set = font_set if subtitles_list else set()

        if pro_mode and not gensettings_for_all_setted:
            user_requests3(video, audio_list, subtitles_list, font_set)

        if video.suffix == '.mkv':
            result = processing_linked_video(video, audio_list, subtitles_list, font_set)
            if result:
                output, video_to_merge_list, retimed_audio_list, retimed_sub_list, count_insert_audio, count_insert_sub = result
            else:
                if not audio_list and not subtitles_list:
                    continue #пропускаем генерацию если видео нелинкованное и нет аудио или сабов
                output = set_output_path(video, audio_list, subtitles_list, font_set)
        else:
            output = set_output_path(video, audio_list, subtitles_list, font_set)

        if output.exists():
            count += 1
            if not output == video:
                gen_before_count += 1
            continue #пропускаем генерацию если файл уже существует

        if video.suffix == '.mkv' and result:
            audio_list = retimed_audio_list
            subtitles_list = retimed_sub_list
            count_inserted = 0
            while count_inserted < count_insert_audio:
                audio_trackname_list.insert(0, "")
                count_inserted += 1
            count_inserted = 0
            while count_inserted < count_insert_sub:
                subtitles_trackname_list.insert(0, "")
                count_inserted += 1

        merge_all_files(output, video_to_merge_list, audio_list, audio_trackname_list, subtitles_list, subtitles_trackname_list, font_set)
        count += 1
        generated_count += 1
        if generated_count >= limit_video_generating:
            break
    return gen_before_count, generated_count

def main():
    global START_DIRECTORY, save_dir, pro_mode, limit_video_generating, save_orig_audio, save_orig_sub, save_orig_font, gensettings_for_all_setted
    lmsg = "Usage: python generate-video-with-these-files.py <mode> <start-dir> <save-dir>"
    if len(sys.argv) > 4:
        print(f"Incorrect argument length! {lmsg}")
        sys.exit(1)

    if len(sys.argv) > 1 and 'default' in sys.argv[1].lower():
        pro_mode = False
    else:
        pro_mode = True

    lmsg2 = f"Incorrect start directory arg! {lmsg}"
    if len(sys.argv) > 2:
        try:
            START_DIRECTORY = Path(sys.argv[2])
            if not START_DIRECTORY.exists():
                print(lmsg2)
                sys.exit(1)
        except Exception:
            print(lmsg2)
            sys.exit(1)
    else:
        START_DIRECTORY = Path(__file__).resolve().parent

    lmsg2 = f"Incorrect save directory arg! {lmsg}"
    if len(sys.argv) > 3:
        try:
            save_dir = Path(sys.argv[3])
            if not save_dir.exists():
                print(lmsg2)
                sys.exit(1)
        except Exception:
            print(lmsg2)
            sys.exit(1)
    else:
        save_dir = START_DIRECTORY

    #значения по умолчанию
    limit_video_generating = 99999
    save_orig_audio = False
    save_orig_sub = False
    save_orig_font = True
    gensettings_for_all_setted = False

    delete_temp_files(save_dir)
    create_message_dictionary()
    set_mkvtools_paths()
    if pro_mode:
        user_requests()

    print(f"Trying to generate a new video in the save directory '{str(save_dir)}' using files from the start directory '{str(START_DIRECTORY)}'.")
    args = get_file_list_dictionarys()
    gen_before_count, generated_count = set_flags_call_merge(*args)
    delete_temp_files(save_dir)

    if generated_count:
        print(f"\nThe script was executed successfully. {generated_count} video files were generated in the directory '{str(save_dir)}'")
    else:
        print(msg[8])
    if gen_before_count:
        print(f"{gen_before_count} video files in the save directory '{str(save_dir)}' had generated names before the current run of the script. Generation for these files has been skipped.")

if __name__ == "__main__":
    main()
