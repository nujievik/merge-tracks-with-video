"""
generate-video-with-these-files-v0.4.4
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

EXTENSIONS = {
    'video': {'.mkv', '.m4v', '.mp4', '.avi', '.h264', '.hevc', '.ts', '.3gp',
              '.flv', '.m2ts', '.mpeg', '.mpg', '.mov', '.ogm', '.webm'},

    'audio': {'.mka', '.m4a', '.aac', '.ac3', '.dts', '.dtshd', '.eac3', '.ec3', '.flac',
                '.mp2', '.mpa', '.mp3', '.opus', '.truehd', '.wav', '.3gp', '.flv', '.m2ts',
                '.mkv', '.mp4', '.mpeg', '.mpg', '.mov', '.ts', '.ogg', '.ogm', '.webm'},

    'container': {'.mkv', '.mp4', '.avi', '.3gp', '.flv', '.m2ts', '.mpeg', '.mpg', '.mov',
                    '.ogg', '.ogm', '.ts', '.webm', '.wmv'},

    'subtitles': {'.ass', '.mks', '.ssa', '.sub', '.srt'},

    'font': {'.ttf', '.otf'}
}

KEYS = {
    'search_subdir': ['надписи', 'sign', 'russiansub', 'russub', "субтит", 'sub'],

    'skipdir_long': {"bonus", "бонус", "special", "bdmenu", "commentary", "creditless"},

    'skipdir_short': {"nc", "nd", "op", "pv"},

    'skip_file': {"_replaced_", "_merged_", "_added_", "_temp_"}
}

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

def delete_temp_files(directory):
    try:
        for filepath in directory.iterdir():
            if filepath.name.startswith("_temp_") and filepath.is_file():
                filepath.unlink()
    except Exception as e:
        print(f"Error: {e}")

class Converter:
    @staticmethod
    def str_to_path(str_in, check_exists=False):
        try:
            path_out = Path(str_in)
            if check_exists and not path_out.exists():
                print("Error. Path not exists!")
                return None
        except Exception:
            return None

        return path_out

    @staticmethod
    def str_to_number(str_in, int_num=True, positive=True):
        try:
            number = int(str_in) if int_num else float(str_in)
            if positive and number <= 0:
                return None
        except Exception:
            return None

        return number

    @staticmethod
    def timedelta_to_str(td):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int(td.microseconds / 1000)
        return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds // 10:02}"  # Два знака после точки

    @staticmethod
    def str_to_timedelta(time_str):
        hours, minutes, seconds = time_str.split(':')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        return timedelta(seconds=total_seconds)

class TxtUtils:
    @staticmethod
    def write_lines_to_file(filepath, *args):
        with open(filepath, 'w', encoding='utf-8') as file:
            for line in args:
                file.write(f"{line}\n")

    @staticmethod
    def add_lines_to_file(filepath, *args):
        with open(filepath, 'a', encoding='utf-8') as file:
            for line in args:
                file.write(f"{line}\n")

    @staticmethod
    def read_lines_from_file(filepath, num_lines):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            # Проверяем, что в файле достаточно строк
            if len(lines) >= num_lines:
                return [line.strip() for line in lines[:num_lines]]
            else:
                return None

        except FileNotFoundError:
            return None

class FileInfo:
    @staticmethod
    def file_have_video_track(filepath):
        command = [str(Tools.mkvmerge), "-i", str(filepath)]
        return True if "video" in get_stdout(command) else False

    @staticmethod
    def get_track_type_id(filepath, track_type):
        id_list = []
        pattern = r"Track ID (\d+):"
        mkvmerge_stdout = get_stdout([str(Tools.mkvmerge), "-i", str(filepath)])
        for line in mkvmerge_stdout.splitlines():
            if track_type in line:
                match = re.search(pattern, line)
                if match:
                    id_list.append(int(match.group(1)))
        return id_list

    @staticmethod
    def get_file_info(filepath, search_query):
        mkvinfo_stdout = get_stdout([str(Tools.mkvinfo), str(filepath)])
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
                        file_duration_timedelta = Converter.str_to_timedelta(file_duration)
                        return file_duration_timedelta

                if "Name:" in search_query:
                    return True
        return None

class Tools():
    mkvextract = None
    mkvinfo = None
    mkvmerge = None

    @staticmethod
    def available_tool(tool):
        try:
            subprocess.run([str(tool), "-h"], check=True, stdout=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    @classmethod
    def find_tool(cls, tool):
        if os.name == 'nt':  # Windows
            potential_paths = [
                Path(os.environ.get("PROGRAMFILES", "")) / "MkvToolNix" / f"{tool}.exe",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "MkvToolNix" / f"{tool}.exe",
                Path.home() / 'Downloads' / 'mkvtoolnix' / f"{tool}.exe"
            ]
            for path in potential_paths:
                if path.exists() and cls.available_tool(path):
                    return path
        return None

    @classmethod
    def set_mkvtools_paths(cls):
        if cls.available_tool("mkvextract"):
            cls.mkvextract = "mkvextract"
        else:
            cls.mkvextract = cls.find_tool("mkvextract")

        if cls.available_tool("mkvinfo"):
            cls.mkvinfo = "mkvinfo"
        else:
            cls.mkvinfo = cls.find_tool("mkvinfo")

        if cls.available_tool("mkvmerge"):
            cls.mkvmerge = "mkvmerge"
        else:
            cls.mkvmerge = cls.find_tool("mkvmerge")

        if None in [cls.mkvextract, cls.mkvinfo, cls.mkvmerge]:
            print("Error! MKVToolNix is not installed. Please install MKVToolNix "
                "and re-run the script:\nhttps://mkvtoolnix.download/downloads.html")
            sys.exit(1)

class Messages():
    msg = {}

    @classmethod
    def create_dictionary(cls, flags):
        cls.msg = {
            1: "[Enter] - use a default value.",
            2: "DefaultAll - use default values for ALL next options."
            }
        cls.msg[3] = f"\n{cls.msg[1]}\n{cls.msg[2]}\n\n"
        cls.msg[4] = "Use a default value.\n"
        cls.msg[5] = f"{cls.msg[4]}All next options will be use default values.\n"
        cls.msg[6] = f"\n{cls.msg[1]}\n{cls.msg[2]}\nSetAll - set next generate settings for all next files.\n\n"
        cls.msg[7] = "Next generate settings will be set for all next files."
        cls.msg[8] = f"Files for generating a new video not found. Checked the directory '{str(flags.flag("start_dir"))}', its subdirectories and {flags.flag("limit_search_dir_up")} directories up."

class Flags():
    def __init__(self):
        self.__flags = {
            "count_sys_argv": 0,
            "start_dir": None,
            "save_dir": None,
            "pro_mode": False,
            "limit_search_dir_up": 3,
            "limit_generate": 99999,
            "count_generated": 0,
            "count_gen_before": 0,
            "video_dir_found": False,
            "audio_dir_found": False,
            "subtitles_dir_found": False,
            "font_dir_found": False,
            "save_global_tags": True,
            "save_chapters": True,
            "save_audio": True,
            "save_original_audio": True,
            "save_subtitles": True,
            "save_original_subtitles": True,
            "save_fonts": True,
            "save_original_fonts": True,
            "save_attachments": True,
            "save_original_attachments": True,
            "add_msg_setall": False,
            "gensettings_for_all_will_be_set": True,
            "gensettings_for_all_setted": False
        }

    sync_flag_dict = {
        "save_fonts": ["save_attachments"],
        "save_attachments": ["save_fonts"],
        "save_original_fonts": ["save_original_attachments"],
        "save_original_attachments": "save_original_fonts"
        }

    argv_count_dict = {
        "--limit-generate=": "limit_generate",
        "--limit-search-up=": "limit_search_dir_up"
        }

    def set_flag(self, key, value):
        if key in self.__flags:
            self.__flags[key] = value
            if key in Flags.sync_flag_dict:
                sync_keys = Flags.sync_flag_dict[key]
                for skey in sync_keys:
                    self.__flags[skey] = value
        else:
            print(f"Error flag '{key}' not found, flag not set.")

    def flag(self, key):
        if not key in self.__flags:
            print(f"Flag '{key}' not found, return None.")
        return self.__flags.get(key, None)

    def processing_sys_argv(self):
        self.set_flag("count_sys_argv", len(sys.argv))
        lmsg = "Usage: python generate-video-with-these-files.py <mode> <start-dir> <save-dir> <*args>"

        if self.flag("count_sys_argv") > 1 and 'default' in sys.argv[1].lower():
            self.set_flag("pro_mode", False)
        else:
            self.set_flag("pro_mode", True)

        if self.flag("count_sys_argv") > 2:
            start_dir = Converter.str_to_path(sys.argv[2])
            if start_dir:
                self.set_flag("start_dir", start_dir)
            else:
                print(f"Incorrect start directory arg! {lmsg}")
                sys.exit(1)
        else:
            self.set_flag("start_dir", Path(__file__).resolve().parent)

        if self.flag("count_sys_argv") > 3:
            save_dir = Converter.str_to_path(sys.argv[3])
            if save_dir:
                self.set_flag("save_dir", save_dir)
            else:
                print(f"Incorrect save directory arg! {lmsg}")
                sys.exit(1)
        else:
            self.set_flag("save_dir", self.flag("start_dir"))

        if self.flag("count_sys_argv") > 4:
            self.set_flag("pro_mode", True)
            self.set_flag("gensettings_for_all_setted", True)

            args = set(sys.argv[4:])
            for arg in args:
                if arg.startswith("--save-"):
                    state = True
                    clean_arg = arg.replace("--save-", "save_")
                else:
                    state = False
                    clean_arg = arg.replace("--no-", "save_")
                clean_arg = clean_arg.replace("-", "_")

                if clean_arg in self.__flags:
                    self.set_flag(clean_arg, state)
                    continue

                index = arg.find("=")
                if index != -1:
                    key = arg[:index + 1]
                    str_number = arg[index + 1:]
                    number = Converter.str_to_number(str_number)
                    if number and key in Flags.argv_count_dict:
                        self.set_flag(Flags.argv_count_dict[key], number)
                        continue

                print(f"Unrecognized argv {arg}, skip this.")

class Requests(Flags):
    @staticmethod
    def clear_console():
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix
            os.system('clear')

    def set_flag_by_user_input(self, flag, default, is_number=False, is_dir=False, is_yes_no=False):
        self.lmsg = ""
        while True:
            user_input = input("> ")

            if user_input.lower() == "defaultall":
                self.lmsg = Messages.msg[5]
                self.set_flag(flag, default)
                self.set_flag("pro_mode", False)

            elif user_input.lower() == "setall" and self.flag("add_msg_setall"):
                print(Messages.msg[7] + "\nPlease enter a value for the current option.")
                self.up_msg = Messages.msg[3]
                self.set_flag("add_msg_setall", False)
                self.set_flag("gensettings_for_all_will_be_set", True)
                continue

            elif user_input == "":
                self.lmsg = Messages.msg[4]
                self.set_flag(flag, default)

            elif is_number:
                number = Converter.str_to_number(user_input)
                if number:
                    self.set_flag(flag, number)
                else:
                    print("Please enter a positive number! Try again.")
                    continue

            elif is_dir:
                path = Converter.str_to_path(user_input)
                if path:
                    self.set_flag(flag, path)
                else:
                    print("Please enter a correct path! Try again.")
                    continue

            elif is_yes_no:
                if user_input.lower() not in ("yes", "y", "no", "n"):
                    print("Incorrect input! Try again.")
                    continue
                elif user_input.lower() in ("yes", "y"):
                    self.set_flag(flag, True)
                else:
                    self.set_flag(flag, False)

            else:
                ("Error. Incorrect call set_flag_by_user_input.")
            return

    def user_requests1(self):
        Requests.clear_console()

        if self.flag("count_sys_argv") < 2:
            user_input = input(f"{Messages.msg[1]}\n\nSelect mode:\n 0 - Default mode\n 1 - PRO mode\n> ")
            Requests.clear_console()
            if user_input not in ("1", "0", ""):
                print("Incorrect input!")
            if user_input == "1":
                print("PRO mode set.")
                self.set_flag("pro_mode", True)
            else:
                print("Default mode set.")
                self.set_flag("pro_mode", False)
                return

        if self.flag("count_sys_argv") < 3:
            print(f"{Messages.msg[3]}Enter the limit number of files to generate:")
            self.set_flag_by_user_input("limit_generate", 99999, is_number=True)
            limit = self.flag("limit_generate") if self.flag("limit_generate") != 99999 else "all"
            Requests.clear_console()
            print(f"{self.lmsg}Generate will be executed for {limit} files.")
            if not self.flag("pro_mode"):
                return

        print(f"{Messages.msg[3]}Enter the save directory for generated files:")
        self.set_flag_by_user_input("save_dir", self.flag("save_dir"), is_dir=True)
        Requests.clear_console()
        print(f"{self.lmsg}The save directory has been set to {self.flag("save_dir")}.\n")
        if not self.flag("pro_mode"):
            return

    def user_requests2(self, vid):
        print("\nFound video files:")
        for video in vid.video_list:
            print(str(video))

        print(f"{Messages.msg[3]}Do you want set generate settings for ALL these video? [y/n]. If not, you must be set settings for each video.")
        self.set_flag_by_user_input("gensettings_for_all_will_be_set", True, is_yes_no=True)
        tale = "all files." if self.flag("gensettings_for_all_will_be_set") else "each file separate."
        Requests.clear_console()
        print(f"{self.lmsg}Generate settings will be set for {tale}")
        if not self.flag("pro_mode"):
            return

        if not self.flag("gensettings_for_all_will_be_set"):
            self.set_flag("add_msg_setall", True)

    def user_requests3(self, vid):
        output_str = f"\nProcessed files:\nVideo: \n{str(vid.video)}"
        if vid.audio_list:
            output_str = output_str + "\nAudio: \n" + "\n".join([str(audio) for audio in vid.audio_list])
        if vid.subtitles_list:
            output_str = output_str + "\nSubtitle: \n" + "\n".join([str(sub) for sub in vid.subtitles_list])
            if vid.font_set:
                output_str = output_str + "\nFont: \n" + "\n".join([str(font) for font in vid.font_set])
        output_str = output_str + "\n"

        self.up_msg = Messages.msg[6] if self.flag("add_msg_setall") else Messages.msg[3]

        print(f"{output_str}{self.up_msg}Do you want to save original audio? [y/n]")
        def_flag = not self.flag("audio_dir_found") or not vid.audio_list
        self.set_flag_by_user_input("save_original_audio", def_flag, is_yes_no=True)
        tale = "be save." if self.flag("save_original_audio") else "NOT be save."
        Requests.clear_console()
        print(f"{self.lmsg}Original audio will {tale}")
        if not self.flag("pro_mode"):
            return

        print(f"{output_str}{self.up_msg}Do you want to save original subtitles? [y/n]")
        def_flag = not self.flag("subtitles_dir_found") or not vid.subtitles_list
        self.set_flag_by_user_input("save_original_subtitles", def_flag, is_yes_no=True)
        tale = "be save." if self.flag("save_original_subtitles") else "NOT be save."
        Requests.clear_console()
        print(f"{self.lmsg}Original subtitles will {tale}")
        if not self.flag("pro_mode"):
            return

        if self.flag("save_original_subtitles"):
            self.set_flag("save_original_fonts", True)

        elif not self.flag("save_original_subtitles") and not vid.subtitles_list:
            self.set_flag("save_original_fonts", False)

        else:
            print(f"{output_str}{self.up_msg}Do you want to save original fonts? External subtitles also will be used original fonts. [y/n]")
            self.set_flag_by_user_input("save_original_fonts", True, is_yes_no=True)
            tale = "be save." if self.flag("save_original_fonts") else "NOT be save."
            Requests.clear_console()
            print(f"{self.lmsg}Original fonts will {tale}")

        if self.flag("gensettings_for_all_will_be_set"):
            self.set_flag("gensettings_for_all_setted", True)

class FileDictionary:
    def __init__(self, flags):
        self.flags = flags
        self.video_list = []
        self.audio_dictionary = {}
        self.audio_trackname_dictionary = {}
        self.subtitles_dictionary = {}
        self.sub_trackname_dictionary = {}
        self.font_set = set()
        self.create_file_list_set_dictionaries()

    @staticmethod
    def clean_tail(tail):
        execute = True
        while execute:
            if re.match(r'^\..{3}\..*$', tail):
                tail = tail[4:]
            else:
                execute = False

        for ext in EXTENSIONS['video'] | EXTENSIONS['audio'] | EXTENSIONS['subtitles']:
            if tail.lower().startswith(ext):
                tail = tail[len(ext):]
            if tail.lower().endswith(ext):
                tail = tail[:-len(ext)]

        tail = tail.strip(' _.')
        if tail.startswith('[') and tail.endswith(']') and tail.count('[') == 1:
            tail = tail.strip('[]')
        return tail

    @staticmethod
    def clean_dirname(dir_name):
        if dir_name.startswith('[') and dir_name.endswith(']') and dir_name.count('[') == 1:
            cleaned_dir_name = dir_name.strip(' _.[]')
        else:
            cleaned_dir_name = dir_name.strip(' _.')
        return cleaned_dir_name

    @staticmethod
    def remove_repeat_fonts(font_set):
        stems = set()
        cleaned_set = set()
        for font in font_set:
            if not font.stem in stems:
                stems.add(font.stem)
                cleaned_set.add(font)
        return cleaned_set

    @staticmethod
    def find_subdirectories_by_string(base_dir):
        search_method = base_dir.glob('*')
        found_dir_list = []
        repeat_search = True
        while repeat_search:
            repeat_search = False
            for subdir in sorted(search_method, reverse=True):
                cln_subdir_name = re.sub(r"[ .]", "", subdir.name).lower()
                for key in KEYS['search_subdir']:
                    if key in cln_subdir_name and subdir.is_dir():
                        found_dir_list.append(subdir)
                        search_method = subdir.rglob('*')
                        repeat_search = True
                        break
                if repeat_search:
                    break

        return found_dir_list

    @staticmethod
    def path_contains_keyword(base_dir, filepath):
        tail_path_str = str(filepath).replace(str(base_dir), "")
        tail_path = Path(tail_path_str)
        search_str = str(tail_path.parent).lower().replace(" ", "")

        if any(key in search_str for key in KEYS['skipdir_long']):
            return True

        while tail_path != tail_path.parent:
            tail_path = tail_path.parent
            search_str = tail_path.name.lower().replace(" ", "")
            if any(key == search_str for key in KEYS['skipdir_short']):
                return True
        return False

    @classmethod
    def find_files_with_extensions(cls, search_dir, extensions, search_name="", recursive_search=False):
        search_method = search_dir.rglob('*') if recursive_search else search_dir.glob('*')
        found_files_list = []
        for filepath in sorted(search_method):
            if recursive_search and cls.path_contains_keyword(search_dir, filepath):
                continue

            filename = filepath.stem
            #если найденный файл содержит служебное имя пропускаем
            if any(key in filename for key in KEYS['skip_file']):
                continue

            if (search_name in filename or filename in search_name) and filepath.is_file() and filepath.suffix in extensions:
                found_files_list.append(filepath)
        return found_files_list

    @classmethod
    def search_video_dir_upper(cls, flags, directory, extensions):
        filepath_list = cls.find_files_with_extensions(directory, extensions)
        for filepath in filepath_list:
            count = 0
            search_dir = directory
            while count <= flags.flag("limit_search_dir_up"):
                video_list = cls.find_files_with_extensions(search_dir, EXTENSIONS['video'], filepath.stem)
                for video in video_list:
                    #не выполняем если видео совпадает с файлом
                    if video == filepath:
                        continue
                    #проверяем что в видео есть видеодорожка, если нужно
                    if video.suffix not in EXTENSIONS['container'] or video.parent != directory or FileInfo.file_have_video_track(video):
                        return video.parent

                search_dir = search_dir.parent
                count += 1
        return None

    @classmethod
    def find_dir_with_filename_to_videoname(cls, video_list, search_dir, search_extensions, recursive_search):
        new_found_list = []
        for video in video_list:
            found_list = cls.find_files_with_extensions(search_dir, search_extensions, video.stem, recursive_search)
            for found in found_list:
                #если найденный файл == видео пропускаем
                if found == video:
                    continue
                #проверяем что в видео есть видеодорожка, если нужно
                if video.suffix not in EXTENSIONS['container'] or video.parent != search_dir or FileInfo.file_have_video_track(video):
                    return found.parent
        return None

    @classmethod
    def search_subdir_when_adir_start_dir(cls, audio_dir, video_dir):
        recursive_search = False
        video_list = cls.find_files_with_extensions(video_dir, EXTENSIONS['video'])
        if video_dir == audio_dir:
            subtitles_dir = cls.find_dir_with_filename_to_videoname(video_list, audio_dir, EXTENSIONS['subtitles'], recursive_search)
            if subtitles_dir:
                return subtitles_dir
            else:
                return None

        search_dir_list = [audio_dir, video_dir]
        #поиск в стартовой директории и в видеодир без рекурсии
        for search_dir in search_dir_list:
            subtitles_dir = cls.find_dir_with_filename_to_videoname(video_list, search_dir, EXTENSIONS['subtitles'], recursive_search)
            if subtitles_dir:
                return subtitles_dir

        #поиск в сабдиректориях по запросу с рекурсией
        search_dir_list = [video_dir] + cls.find_subdirectories_by_string(video_dir)
        for search_dir in reversed(search_dir_list):
            for recursive_search in [False, True]:
                subtitles_dir = cls.find_dir_with_filename_to_videoname(video_list, search_dir, EXTENSIONS['subtitles'], recursive_search=recursive_search)
                if subtitles_dir:
                    return subtitles_dir
        return None

    @classmethod
    def find_font_directory(cls, subtitles_dir, video_dir):
        font_list = cls.find_files_with_extensions(subtitles_dir, EXTENSIONS['font'], "", recursive_search=True)
        if font_list:
            return font_list[0].parent
        else:
            if subtitles_dir != video_dir:
                font_list = cls.find_files_with_extensions(subtitles_dir.parent, EXTENSIONS['font'], "", recursive_search=True)
            if font_list:
                return font_list[0].parent
        return None

    @classmethod
    def collect_files_from_found_directories(cls, audio_dir, subtitles_dir, font_dir):
        audio_list = []
        subtitles_list = []
        font_set = set()

        recursive_search=False
        if audio_dir:
            audio_list = cls.find_files_with_extensions(audio_dir, EXTENSIONS['audio'], "", recursive_search)
        if subtitles_dir:
            subtitles_list = cls.find_files_with_extensions(subtitles_dir, EXTENSIONS['subtitles'], "", recursive_search)
        if font_dir:
            font_set = set(cls.find_files_with_extensions(font_dir, EXTENSIONS['font'], "", recursive_search))
        return audio_list, subtitles_list, font_set

    @classmethod
    def collect_files_from_start_dir(cls, search_dir):
        recursive_search = True
        audio_list = cls.find_files_with_extensions(search_dir, EXTENSIONS['audio'], "", recursive_search)
        subtitles_list = cls.find_files_with_extensions(search_dir, EXTENSIONS['subtitles'], "", recursive_search)
        font_set = set(cls.find_files_with_extensions(search_dir, EXTENSIONS['font'], "", recursive_search))
        return audio_list, subtitles_list, font_set

    @classmethod
    def get_trackname(cls, tail, dir_name):
        tail = cls.clean_tail(tail) if len(tail) > 2 else tail
        if len(tail) > 2:
            trackname = tail
        else:
            trackname = cls.clean_dirname(dir_name)
        return trackname

    @classmethod
    def create_dictionaries(cls, video_list, audio_list, subtitles_list):
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
            audio_dictionary[str(video)] = []
            audio_trackname_dictionary[str(video)] = []
            subtitles_dictionary[str(video)] = []
            sub_trackname_dictionary[str(video)] = []

            for audio in audio_list:
                #если audio совпадает с video пропускаем audio или video
                if video == audio:
                    if found_video_track or FileInfo.file_have_video_track(video):
                        found_video_track = True
                        continue
                    else:
                        skip_video = True
                        break

                if video.stem in audio.stem:
                    audio_dictionary[str(video)].append(audio)
                    tail = audio.stem[len(video.stem):]
                    dir_name = audio.parent.name
                    trackname = cls.get_trackname(tail, dir_name)
                    audio_trackname_dictionary[str(video)].append(trackname)
                    save_video = True

            if skip_video:
                continue

            for subtitles in subtitles_list:
                #если имена частично совпадают
                if video.stem in subtitles.stem:
                    subtitles_dictionary[str(video)].append(subtitles)
                    tail = subtitles.stem[len(video.stem):]
                    dir_name = subtitles.parent.name
                    trackname = cls.get_trackname(tail, dir_name)
                    sub_trackname_dictionary[str(video)].append(trackname)
                    save_video = True

            if save_video:
                new_video_list.append(video)
                count += 1

        return new_video_list, audio_dictionary, audio_trackname_dictionary, subtitles_dictionary, sub_trackname_dictionary

    def find_directories(self):
        self.video_dir = None
        self.audio_dir = None
        self.subtitles_dir = None
        self.font_dir = None
        search_dir = self.flags.flag("start_dir")

        # Поиск видеодиректории через аудио
        self.video_dir = FileDictionary.search_video_dir_upper(self.flags, search_dir, EXTENSIONS['audio'])
        if self.video_dir:
            self.flags.set_flag("video_dir_found", True)
            self.flags.set_flag("audio_dir_found", True)
            self.audio_dir = search_dir

            self.subtitles_dir = FileDictionary.search_subdir_when_adir_start_dir(self.audio_dir, self.video_dir)
            if self.subtitles_dir:
                self.flags.set_flag("subtitles_dir_found", True)

        else: # Поиск видеодиректории через сабы
            self.video_dir = FileDictionary.search_video_dir_upper(self.flags, search_dir, EXTENSIONS['subtitles'])
            if self.video_dir:
                self.flags.set_flag("video_dir_found", True)
                self.flags.set_flag("subtitles_dir_found", True)
                self.subtitles_dir = search_dir

        # Если найден сабдир, ищем фонтдир
        if self.flags.flag("subtitles_dir_found"):
            self.font_dir = FileDictionary.find_font_directory(self.subtitles_dir, self.video_dir)
            if self.font_dir:
                self.flags.set_flag("font_dir_found", True)

    def create_file_list_set_dictionaries(self):
        self.find_directories()

        search_dir = self.video_dir if self.video_dir else self.flags.flag("start_dir")
        video_list = FileDictionary.find_files_with_extensions(search_dir, EXTENSIONS['video'])
        if not video_list:
            print(Messages.msg[8])
            sys.exit(0)

        if self.flags.flag("audio_dir_found") or self.flags.flag("subtitles_dir_found"):
            audio_list, subtitles_list, self.font_set = FileDictionary.collect_files_from_found_directories(self.audio_dir, self.subtitles_dir, self.font_dir)

        else:
            audio_list, subtitles_list, font_set = FileDictionary.collect_files_from_start_dir(self.flags.flag("start_dir"))
            if font_set:
                self.font_set = FileDictionary.remove_repeat_fonts(font_set)

        self.video_list, self.audio_dictionary, self.audio_trackname_dictionary, self.subtitles_dictionary, self.sub_trackname_dictionary = FileDictionary.create_dictionaries(video_list, audio_list, subtitles_list)

        if not self.video_list: #пробуем найти mkv для обработки линковки
            self.audio_dictionary = self.audio_trackname_dictionary = self.subtitles_dictionary = self.sub_trackname_dictionary = self.font_set = {}
            self.video_list = FileDictionary.find_files_with_extensions(self.flags.flag("start_dir"), ".mkv")
            if not self.video_list:
                print(Messages.msg[8])
                sys.exit(0)

class Merge(FileDictionary):
    def set_output_path(self, tail=""):
        partname = f"{self.video.stem}{tail}"
        if self.audio_list and self.flags.flag("save_audio"):
            if self.flags.flag("save_original_audio"):
                partname = partname + "_added_audio"
            else:
                partname = partname + "_replaced_audio"

        if self.subtitles_list and self.flags.flag("save_subtitles"):
            if self.flags.flag("save_original_subtitles"):
                partname = partname + "_added_subs"
            else:
                partname = partname + "_replaced_subs"

        if self.font_set and self.flags.flag("save_fonts"):
            if self.flags.flag("save_original_fonts"):
                partname = partname + "_added_fonts"
            else:
                partname = partname + "_replaced_fonts"

        self.output = Path(self.flags.flag("save_dir")) / f"{partname}.mkv"

    def execute_merge(self, coding_cp1251=False, opt_sub={}):
        command = [str(Tools.mkvmerge), "-o", str(self.output)]
        if not self.flags.flag("save_global_tags"):
            command.append("--no-global-tags")
        if not self.flags.flag("save_chapters"):
            command.append("--no-chapters")
        if not self.flags.flag("save_original_audio"):
            command.append("--no-audio")
        if not self.flags.flag("save_original_subtitles"):
            command.append("--no-subtitles")
        if not self.flags.flag("save_original_fonts"):
            command.append("--no-attachments")

        #добавляем видеофайлы
        command.append(str(self.merge_video_list[0]))
        for video in self.merge_video_list[1:]:
            command.append(f"+{str(video)}")

        if self.flags.flag("save_audio"): #add audio
            count = 0
            for audio in self.audio_list:
                track_name = self.audio_trackname_list[count]
                if track_name and not (audio.suffix in (".mka", ".mkv") and FileInfo.get_file_info(audio, "Name:")):
                    track_id_list = FileInfo.get_track_type_id(audio, "audio") #получаем инфу об аудиотреках
                    for track_id in track_id_list:
                        command.extend(["--track-name", f"{track_id}:{track_name}", str(audio)])
                else:
                    command.append(str(audio))
                count += 1

        if self.flags.flag("save_subtitles"): #add subtitles
            count = 0
            for sub in self.subtitles_list:
                opt_id = opt_sub.get(str(sub), None)
                if opt_id:
                    command.extend(["--sub-charset", f"{opt_id}:windows-1251"])

                track_name = self.sub_trackname_list[count]
                if track_name and not (sub.suffix in (".mks", ".mkv") and FileInfo.get_file_info(sub, "Name:")):
                    track_id_list = FileInfo.get_track_type_id(sub, "subtitles")
                    for track_id in track_id_list:
                        command.extend(["--track-name", f"{track_id}:{track_name}", str(sub)])
                else:
                    command.append(str(sub))
                count += 1

        if self.flags.flag("save_fonts"):
            for font in self.font_set:
                command.extend(["--attach-file", str(font)])

        print(f"\nGenerating a merged video file using mkvmerge. Executing the command: \n{command}")

        lmsg = f"The command was executed successfully. The generated video file was saved to:\n{str(self.output)}"
        try:
            command_out = subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout.decode()
            if self.flags.flag("pro_mode"):
                print(command_out)
            print(lmsg)

        except subprocess.CalledProcessError as e:
            command_out = e.output.decode()
            if self.flags.flag("pro_mode"):
                print(command_out)
            cleaned_out = ''.join(command_out.split()).lower()
            last_line_out = command_out.splitlines()[-1]
            cleaned_lline_out = ''.join(last_line_out.split()).lower()

            if not coding_cp1251 and "textsubtitletrackcontainsinvalid8-bitcharacters" in cleaned_out:
                print("Invalid 8-bit characters in subtitles file!\nTrying to generate with windows-1251 coding.")
                opt_sub = {}
                for line in command_out.splitlines():
                    if line.startswith("Warning") and "invalid 8-bit characters" in line:
                        file_name_match = re.search(r"'(/[^']+)'", line)
                        file_name = file_name_match.group(1) if file_name_match else None
                        file_path = Path(file_name)

                        track_id_match = re.search(r"track (\d+)", line)
                        track_id = track_id_match.group(1) if track_id_match else None
                        if file_name:
                            opt_sub[f'{str(file_path)}'] = None
                            if track_id:
                                opt_sub[f'{str(file_path)}'] = track_id
                self.execute_merge(coding_cp1251=True, opt_sub=opt_sub)
                return

            if not cleaned_lline_out.startswith("error"):
                print(lmsg)

                if "thecodec'sprivatedatadoesnotmatch" in cleaned_out:
                    print(f"Attention! The video file maybe corrupted because video parts have mismatched codec parameters. Please check the video file.")

            else:
                if "containschapterswhoseformatwasnotrecognized" in cleaned_lline_out:
                    print(f"{last_line_out}\nTrying to generate without chapters.")
                    self.flags.set_flag("save_chapters", False)
                    self.execute_merge(coding_cp1251=coding_cp1251, opt_sub=opt_sub)
                    self.flags.set_flag("save_chapters", True)

                elif "nospaceleft" in cleaned_lline_out:
                    if self.output.exists():
                        self.output.unlink()
                    delete_temp_files(self.flags.flag("save_dir"))
                    print(f"Error writing file!\nPlease re-run the script with a different save directory.\nExiting the script.")
                    sys.exit(1)

                else:
                    if self.output.exists():
                        self.output.unlink()
                    delete_temp_files(self.flags.flag("save_dir"))
                    print(f"Error executing the command!\n{last_line_out}\nExiting the script.")
                    sys.exit(1)

    def set_merge_flags(self):
        if self.flags.flag("pro_mode"):
            if not self.flags.flag("gensettings_for_all_setted"):
                self.flags.user_requests3(self)
        else:
            save_original_audio = not self.flags.flag("audio_dir_found") or not self.audio_list
            self.flags.set_flag("save_original_audio", save_original_audio)

            save_original_subtitles = not self.flags.flag("subtitles_dir_found") or not self.subtitles_list
            self.flags.set_flag("save_original_subtitles", save_original_subtitles)

            save_fonts = True if self.subtitles_list else False
            self.flags.set_flag("save_fonts", save_fonts)

    def merge_all_files(self):
        count_generated = 0
        count_gen_before = 0
        if self.flags.flag("pro_mode") and not self.flags.flag("gensettings_for_all_setted"):
            self.flags.user_requests2(self)

        for self.video in self.video_list:
            self.merge_video_list = [self.video]
            self.audio_list = self.audio_dictionary.get(str(self.video), [])
            self.audio_trackname_list = self.audio_trackname_dictionary.get(str(self.video), [])
            self.subtitles_list = self.subtitles_dictionary.get(str(self.video), [])
            self.sub_trackname_list = self.sub_trackname_dictionary.get(str(self.video), [])

            self.set_merge_flags()
            if self.video.suffix == ".mkv":
                if not self.processing_linked_video():
                    self.set_output_path()
            else:
                self.set_output_path()

            if self.output.exists():
                count_gen_before += 1
                continue

            self.execute_merge()
            count_generated += 1

            if count_generated >= self.flags.flag("limit_generate"):
                break

        self.flags.set_flag("count_generated", count_generated)
        self.flags.set_flag("count_gen_before", count_gen_before)

class Video(Merge):
    @staticmethod
    def find_video_with_uid(search_dir, target_uid):
        video_list = FileDictionary.find_files_with_extensions(search_dir, ".mkv")
        for video in video_list:
            video_uid = FileInfo.get_file_info(video, "Segment UID")
            if video_uid.lower() == target_uid.lower():
                return video
        return None

    @staticmethod
    def get_segment_info(mkvmerge_stdout, partname, split_start, split_end):
        #ищем переназначения
        timestamps = re.findall(r'Timestamp used in split decision: (\d{2}:\d{2}:\d{2}\.\d{9})', mkvmerge_stdout)
        if len(timestamps) == 2:
            segment = Path(partname.parent) / f"{partname.stem}-002{partname.suffix}"
            defacto_start = Converter.str_to_timedelta(timestamps[0])
            defacto_end = Converter.str_to_timedelta(timestamps[1])
            offset_start = defacto_start - split_start
            offset_end = defacto_end - split_end
        elif len(timestamps) == 1:
            timestamp = Converter.str_to_timedelta(timestamps[0])
            #если переназначение для старта
            if split_start > timedelta(0):
                segment = Path(partname.parent) / f"{partname.stem}-002{partname.suffix}"
                defacto_start = timestamp
                defacto_end = defacto_start + FileInfo.get_file_info(segment, "Duration")
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
            defacto_end = FileInfo.get_file_info(segment, "Duration")
            offset_start = timedelta(0)
            offset_end = timedelta(0)

        return segment, defacto_start, defacto_end, offset_start, offset_end

    @staticmethod
    def extract_track(input_file, output, track_id):
        command = [str(Tools.mkvextract), "tracks", str(input_file), f"{track_id}:{str(output)}"]
        execute_command(command)

    @staticmethod
    def split_file(input_file, partname, start, end, file_type="video", save_original_fonts=True, track_id=""):
        command = [str(Tools.mkvmerge), "-o", str(partname), "--split", f"timecodes:{start},{end}", "--no-global-tags", "--no-chapters", "--no-subtitles"]
        if "video" in file_type:
            command.append("--no-audio")
            if not save_original_fonts:
                command.append("--no-attachments")
        else:
            command.extend(["--no-video", "--no-attachments"])
            if track_id:
                command.extend(["-a", f"{track_id}"])
        command.append(str(input_file))

        # Выполняем команду и ищем переназначения
        mkvmerge_stdout = get_stdout(command)
        segment, defacto_start, defacto_end, offset_start, offset_end = Video.get_segment_info(mkvmerge_stdout, partname, start, end)
        length = defacto_end - defacto_start

        return segment, length, offset_start, offset_end

    @staticmethod
    def merge_file_segments(segment_list, output):
        command = [str(Tools.mkvmerge), "-o", str(output)]
        command.append(segment_list[0])
        for segment in segment_list[1:]:
            command.append(f"+{str(segment)}")
        execute_command(command)

    def extract_chapters(self):
        command = [str(Tools.mkvextract), str(self.video), "chapters", str(self.chapters)]
        execute_command(command)

    def get_chapters_info(self):
        try:
            tree = ET.parse(self.chapters)
        except Exception:
            self.uid_list = self.start_list = self.end_list = []
            return None
        root = tree.getroot()
        self.uid_list = []
        self.start_list = []
        self.end_list = []

        for chapter_atom in root.findall(".//ChapterAtom"):
            chapter_uid = chapter_atom.find("ChapterSegmentUID")
            chapter_uid = chapter_uid.text if chapter_uid is not None else None
            self.uid_list.append(chapter_uid)

            chapter_start = chapter_atom.find("ChapterTimeStart")
            chapter_start = Converter.str_to_timedelta(chapter_start.text) if chapter_start is not None else None
            self.start_list.append(chapter_start)

            chapter_end = chapter_atom.find("ChapterTimeEnd")
            chapter_end = Converter.str_to_timedelta(chapter_end.text) if chapter_end is not None else None
            self.end_list.append(chapter_end)

        if all(uid is None for uid in self.uid_list): #если нет внешних файлов
            self.uid_list = self.start_list = self.end_list = []
            return None

        if None in self.start_list or None in self.end_list:
            temp_start_list = []
            temp_end_list = []
            prev_nonid_end = timedelta(0)
            length = len(self.start_list)
            count = 0
            for start in self.start_list:
                end = self.end_list[count]
                uid = self.uid_list[count]

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
                    if length > count+1 and self.start_list[count+1]:
                        temp_end = self.start_list[count+1]

                    else:
                        if uid:
                            temp_video = Video.find_video_with_uid(self.video.parent, uid)
                            if not temp_video:
                                print(f"Video file with uid {uid} not found in the video directory '{str(self.video.parent)}'\nThis file is part of the linked video '{str(self.video)}' and is required for merging. Please move this file to the video directory and re-run the script.")
                                sys.exit(1)
                        else:
                            temp_video = self.video
                        temp_end = FileInfo.get_file_info(temp_video, "Duration")

                temp_start_list.append(temp_start)
                temp_end_list.append(temp_end)
                if not uid:
                    prev_nonid_end = temp_end
                count += 1
            self.start_list = temp_start_list
            self.end_list = temp_end_list

    def rw_uid_file_info(self):
        self.txt_uid = Path(self.flags.flag("save_dir")) / f"_temp_{self.uid}.txt"
        self.segment = None
        self.length = None
        self.offset_start = None
        self.offset_end = None
        read = TxtUtils.read_lines_from_file(self.txt_uid, 6)
        if read:
            line1, line2, line3, line4, line5, line6 = read
            self.to_split = Path(line1)
            #если время предыдущего сплита совпадает
            if Converter.str_to_timedelta(line2) == self.start and (Converter.str_to_timedelta(line3) == self.end or Converter.str_to_timedelta(line4) <= self.end):
                #и нужный сплит существует не сплитуем
                self.segment = Path(self.flags.flag("save_dir")) / f"_temp_{self.uid}.mkv"
                if self.segment.exists():
                    self.length = Converter.str_to_timedelta(line4)
                    self.offset_start = Converter.str_to_timedelta(line5)
                    self.offset_end = Converter.str_to_timedelta(line6)
                    self.execute_split = False
        else:
            self.to_split = Video.find_video_with_uid(self.video_dir, self.uid)
            TxtUtils.write_lines_to_file(self.txt_uid, self.to_split, self.start, self.end)

    def get_segment_linked_video(self):
        self.execute_split = True
        self.prev_offset_end = self.offset_end
        self.chapter_start = self.start
        self.chapter_end = self.end

        if self.uid:
            self.rw_uid_file_info()
        else:
            self.to_split = self.video
            self.start = self.prev_nonuid_end

        if self.execute_split:
            self.prev_lengths = self.lengths
            self.segment, length, self.offset_start, self.offset_end = Video.split_file(self.to_split, self.partname, self.start, self.end, save_original_fonts=self.flags.flag("save_original_fonts"))
            self.lengths = self.lengths + length

            if self.uid: # сплит по внешнему файлу переименовываем чтоб использовать дальше
                new_path = Path(self.flags.flag("save_dir")) / f"_temp_{self.uid}.mkv"
                if new_path.exists():
                    new_path.unlink()
                self.segment.rename(new_path)
                self.segment = new_path
                TxtUtils.add_lines_to_file(self.txt_uid, self.lengths - self.prev_lengths, self.offset_start, self.offset_end)
        else:
            self.lengths = self.lengths + self.length

        if self.uid:
            self.offset_start = self.prev_offset_end + self.offset_start
            self.offset_end = self.prev_offset_end + self.offset_end
        else:
            self.offset_start = self.start - self.chapter_start + self.offset_start
            self.offset_end = self.offset_end
            self.prev_nonuid_end = self.chapter_end + self.offset_end

    def get_all_segments_linked_video(self):
        self.source_list = []
        self.segment_list = []
        self.offset_start_list = []
        self.offset_end_list = []
        self.lengths_list = []

        self.video_dir = self.video.parent
        self.lengths = timedelta(0)
        self.offset_start = timedelta(0)
        self.offset_end = timedelta(0)
        self.prev_nonuid_end = timedelta(0)
        count = 0
        for self.uid in self.uid_list:
            self.start = self.start_list[count]
            self.end = self.end_list[count]
            self.partname = Path(self.flags.flag("save_dir")) / f"_temp_{count}.mkv"
            self.get_segment_linked_video()

            self.source_list.append(self.to_split)
            self.segment_list.append(self.segment)
            self.offset_start_list.append(self.offset_start)
            self.offset_end_list.append(self.offset_end)
            self.lengths_list.append(self.lengths)
            count += 1

    def get_retimed_segments_orig_audio(self):
        self.a_segment_list = []
        prev_lengths = timedelta(0)
        uid_lengths = timedelta(0)
        a_lengths = timedelta(0)
        count = 0
        for source in self.source_list:
            lengths = self.lengths_list[count]
            length = lengths - prev_lengths
            offset_lengths = a_lengths - prev_lengths

            if source == self.video:
                start = prev_lengths - uid_lengths + offset_lengths if prev_lengths - uid_lengths + offset_lengths > timedelta(0) else timedelta(0)
                end = lengths - uid_lengths
            else:
                start = offset_lengths if offset_lengths > timedelta(0) else timedelta(0)
                end = start + length - offset_lengths if start != timedelta(0) else length
                uid_lengths = uid_lengths + length

            partname = Path(self.flags.flag("save_dir")) / f"_temp_{count}.mka"
            a_segment, a_length, offset_start, offset_end = Video.split_file(source, partname, start, end, file_type="audio", track_id=self.track_id)
            if offset_start > timedelta(milliseconds=200) or offset_end > timedelta(milliseconds=200):
                new_start = start - offset_start if start - offset_start > timedelta(0) else start
                new_end = end - offset_end
                a_segment, a_length, offset_start, offset_end = Video.split_file(source, partname, new_start, new_end, file_type="audio", track_id=self.track_id)

            self.a_segment_list.append(a_segment)
            a_lengths = a_lengths + a_length
            prev_lengths = lengths
            count += 1

    def get_retimed_segments_ext_audio(self):
        start = timedelta(0)
        end = timedelta(0)
        prev_lengths = timedelta(0)
        a_lengths = timedelta(0)
        self.a_segment_list = []

        count = 0
        for lengths in self.lengths_list:
            add_compensation = False
            length = lengths - prev_lengths
            offset_start = self.offset_start_list[count]
            offset_end = self.offset_end_list[count]
            offset_audio_to_video = a_lengths - prev_lengths

            if self.source_list[count] == self.video:
                start = prev_lengths + offset_audio_to_video

                if offset_end > timedelta(milliseconds=2000) and len(self.source_list) > count+2 and self.video == self.source_list[count+2]:
                    end = lengths - offset_end
                    compensation_start = self.lengths_list[count+1] - self.offset_start_list[count+2]
                    add_compensation = True
                else:
                    end = lengths
            else:
                start = prev_lengths - offset_start + offset_audio_to_video
                end = start + length

            partname = Path(self.flags.flag("save_dir")) / f"_temp_{count}.mka"
            a_segment, a_length, split_offset_start, split_offset_end = Video.split_file(self.audio, partname, start, end, file_type="audio")

            if split_offset_start > timedelta(milliseconds=200) or split_offset_end > timedelta(milliseconds=200):
                new_start = start - split_offset_start if start - split_offset_start > timedelta(0) else start
                new_end = end - split_offset_end
                a_segment, a_length, *_ = Video.split_file(self.audio, partname, new_start, new_end, file_type="audio")

            if add_compensation:
                compensation_length = length - a_length
                if compensation_length > timedelta(milliseconds=500):
                    partname = Path(self.flags.flag("save_dir")) / f"_temp_compensation_{count}.mka"
                    compensation_end = compensation_start + compensation_length
                    compensation_segment, compensation_length, *_ = Video.split_file(self.audio, partname, compensation_start, compensation_end, file_type="audio")
                add_compensation = True if compensation_length > timedelta(milliseconds=500) else False

            if add_compensation:
                self.a_segment_list.extend([a_segment, compensation_segment])
                a_lengths = a_lengths + a_length + compensation_length
            else:
                self.a_segment_list.append(a_segment)
                a_lengths = a_lengths + a_length

            prev_lengths = lengths
            count += 1

    def get_retimed_audio_list(self):
        self.retimed_audio_list = []
        count = 0
        if self.flags.flag("save_original_audio"):
            audio_track_id_list = FileInfo.get_track_type_id(self.video, "audio")
            for self.track_id in audio_track_id_list:
                self.get_retimed_segments_orig_audio()
                orig_audio = Path(self.flags.flag("save_dir")) / f"_temp_audio_{count}.mka"
                Video.merge_file_segments(self.a_segment_list, orig_audio)

                self.retimed_audio_list.append(orig_audio)
                self.audio_trackname_list.insert(0, "")
                count += 1

        for self.audio in self.audio_list:
            retimed_audio = Path(self.flags.flag("save_dir")) / f"_temp_audio_{count}.mka"
            self.get_retimed_segments_ext_audio()
            Video.merge_file_segments(self.a_segment_list, retimed_audio)
            self.retimed_audio_list.append(retimed_audio)
            count += 1

    def retime_original_sub(self):
        count = 0
        dictionary = {}
        #считываем все сабы
        for sub in self.segment_orig_sub_list:
            with open(sub, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                dictionary[f"lines{count}"] = lines
                count += 1
        total_lines = list(dictionary.values())

        self.retimed_original_sub = self.segment_orig_sub_list[0]
        with open(self.retimed_original_sub, 'w', encoding='utf-8') as file:
            for line in total_lines[0]:
                if not line.startswith("Dialogue:"):
                    file.write(line) #записываем строки до диалогов
                else:
                    break

            #ретаймим
            count = 0
            prev_lengths = timedelta(0)
            prev_offset_end = timedelta(0)
            uid_lengths = timedelta(0)
            prev_nonuid_offset_end = timedelta(0)
            for lengths in self.lengths_list:
                length = lengths - prev_lengths
                offset_start = self.offset_start_list[count]
                offset_end = self.offset_end_list[count]

                if self.source_list[count] == self.video:
                    start = prev_lengths - uid_lengths if prev_lengths - uid_lengths > timedelta(0) else timedelta(0)
                    retime_offset = (offset_start - prev_nonuid_offset_end) + uid_lengths
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
                        dialogue_time_start = Converter.str_to_timedelta(str_dialogue_time_start)
                        dialogue_time_end = Converter.str_to_timedelta(str_dialogue_time_end)

                        #не включаем строки не входящие в сегмент
                        if dialogue_time_start < remove_border_start and dialogue_time_end < remove_border_start:
                            continue
                        elif dialogue_time_start > remove_border_end and dialogue_time_end > remove_border_end:
                            continue

                        else: #ретаймим и записываем
                            new_dialogue_time_start = dialogue_time_start + retime_offset
                            new_dialogue_time_end = dialogue_time_end + retime_offset
                            str_new_dialogue_time_start = Converter.timedelta_to_str(new_dialogue_time_start)
                            str_new_dialogue_time_end = Converter.timedelta_to_str(new_dialogue_time_end)
                            line = f"{parts[0]},{str_new_dialogue_time_start},{str_new_dialogue_time_end},{','.join(parts[3:])}"
                            file.write(line)

                prev_lengths = lengths
                prev_offset_end = offset_end
                if self.source_list[count] == self.video:
                    prev_nonuid_offset_end = offset_end
                else:
                    uid_lengths = uid_lengths + length
                count += 1

    def retime_external_sub(self):
        with open(self.sub_for_retime, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        self.retimed_external_sub = self.sub_for_retime
        with open(self.retimed_external_sub, 'w', encoding='utf-8') as file:
            for line in lines:
                if not line.startswith("Dialogue:"):
                    file.write(line) #записываем строки до диалогов
                else:
                    break

            prev_lengths = timedelta(0)
            prev_offset_end = timedelta(0)
            count = 0
            for lengths in self.lengths_list:
                length = lengths - prev_lengths
                offset_start = self.offset_start_list[count]
                offset_end = self.offset_end_list[count]

                start = prev_lengths
                end = lengths
                if self.video == self.source_list[count]: #если отрезок из основного файла
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
                        dialogue_time_start = Converter.str_to_timedelta(str_dialogue_time_start)
                        dialogue_time_end = Converter.str_to_timedelta(str_dialogue_time_end)

                        #не включаем строки не входящие в сегмент
                        if dialogue_time_start < remove_border_start and dialogue_time_end < remove_border_start:
                            continue
                        elif dialogue_time_start > remove_border_end and dialogue_time_end > remove_border_end:
                            continue

                        else: #ретаймим и записываем
                            new_dialogue_time_start = dialogue_time_start + retime_offset
                            new_dialogue_time_end = dialogue_time_end + retime_offset
                            str_new_dialogue_time_start = Converter.timedelta_to_str(new_dialogue_time_start)
                            str_new_dialogue_time_end = Converter.timedelta_to_str(new_dialogue_time_end)
                            line = f"{parts[0]},{str_new_dialogue_time_start},{str_new_dialogue_time_end},{','.join(parts[3:])}"
                            file.write(line)
                prev_lengths = lengths
                prev_offset_end = offset_end
                count += 1

    def get_retimed_sub_list(self):
        count = 0
        self.retimed_sub_list = []

        if self.flags.flag("save_original_subtitles"):
            self.segment_orig_sub_list = []

            #проверяем сколько дорожек субтитров в исходном видео
            sub_track_id_list = FileInfo.get_track_type_id(self.video, "subtitles")
            for self.track_id in sub_track_id_list:
                count_temp = 0
                for source in self.source_list:
                    split_original_sub = Path(self.flags.flag("save_dir")) / f"_temp_subtitles_{count + count_temp}.ass"
                    Video.extract_track(source, split_original_sub, self.track_id)
                    self.segment_orig_sub_list.append(split_original_sub)
                    count_temp += 1

                self.retime_original_sub()
                self.retimed_sub_list.append(self.retimed_original_sub)
                self.sub_trackname_list.insert(0, "")
                count += 1

        for subtitles in self.subtitles_list:
            self.sub_for_retime = Path(self.flags.flag("save_dir")) / f"_temp_subtitles_{count}.ass"
            if subtitles.suffix != ".ass":
                print(f"\nSkip subtitles! {str(subtitles)} \nThese subtitles need to be retimed because the video file has segment linking. Retime is only possible for .ass subtitles.")
                continue
            else:
                shutil.copy(subtitles, self.sub_for_retime)

            self.retime_external_sub()
            self.retimed_sub_list.append(self.retimed_external_sub)
            count += 1

    def processing_linked_video(self):
        self.chapters = Path(self.flags.flag("save_dir")) / "_temp_chapters.xml"
        if self.chapters.exists():
            self.chapters.unlink()
        self.extract_chapters()
        if not self.chapters.exists():
            return None

        self.get_chapters_info()
        if not self.uid_list:
            return None
        else:
            self.set_output_path("_merged_video")
            if self.output.exists():
                return self.output

        self.get_all_segments_linked_video()
        self.merge_video_list = self.segment_list

        self.get_retimed_audio_list()
        self.audio_list = self.retimed_audio_list

        self.get_retimed_sub_list()
        self.subtitles_list = self.retimed_sub_list
        return self.output

def main():
    flags = Requests()
    flags.processing_sys_argv()

    Tools.set_mkvtools_paths()
    Messages.create_dictionary(flags)
    if flags.flag("pro_mode") and flags.flag("count_sys_argv") < 4:
        flags.user_requests1()

    print(f"\nTrying to generate a new video in the save directory '{str(flags.flag("save_dir"))}' using files from the start directory '{str(flags.flag("start_dir"))}'.")
    vid = Video(flags)
    vid.merge_all_files()
    delete_temp_files(flags.flag("save_dir"))

    if flags.flag("count_generated"):
        print(f"\nThe script was executed successfully. {flags.flag("count_generated")} video files were generated in the directory '{str(flags.flag("save_dir"))}'")
    else:
        print(Messages.msg[8])

    if flags.flag("count_gen_before"):
        print(f"{flags.flag("count_gen_before")} video files in the save directory '{str(flags.flag("save_dir"))}' had generated names before the current run of the script. Generation for these files has been skipped.")

if __name__ == "__main__":
    main()
