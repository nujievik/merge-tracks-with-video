"""
generate-video-with-these-files-v0.5.1
This program is part of the generate-video-with-these-files-script repository

Licensed under GPL-3.0.
This script requires third-party tools: Python and MKVToolNix.
These tools are licensed under Python PSF and GPL-2, respectively.
See LICENSE file for details.
"""
import sys
import os
import xml.etree.ElementTree as ET
import shutil
import re
import subprocess
import shlex
import uuid
from pathlib import Path
from datetime import timedelta

class CommandExecutor:
    @staticmethod
    def execute(command, exit_when_error=True):
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE)

        except subprocess.CalledProcessError as e:
            if not exit_when_error:
                return False
            print(f"Error executing the command:\n{command}\n{e.output.decode()}\nExiting the script.")
            sys.exit(1)

    @staticmethod
    def get_stdout(command, exit_when_error=True):
        try:
            return subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout.decode()

        except subprocess.CalledProcessError as e:
            if not exit_when_error:
                return e.output.decode(), 1
            print(f"Error executing the command:\n{command}\n{e.output.decode()}\nExiting the script.")
            sys.exit(1)

class TypeConverter:
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
    def str_to_number(str_in, int_num=True, non_negative=True):
        try:
            number = int(str_in) if int_num else float(str_in)
            if non_negative and number < 0:
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

    @staticmethod
    def command_to_print_str(command):
        return f"'{TypeConverter.str_to_path(command[0]).stem}' {' '.join(f"'{str(item)}'" for item in command[1:])}"

class FileInfo:
    @staticmethod
    def file_has_video_track(filepath):
        command = [str(Tools.mkvmerge), "-i", str(filepath)]
        return True if "video" in CommandExecutor.get_stdout(command) else False

    @staticmethod
    def get_track_type_id(filepath, track_type):
        id_list = []
        pattern = r"Track ID (\d+):"
        mkvmerge_stdout = CommandExecutor.get_stdout([str(Tools.mkvmerge), "-i", str(filepath)])
        for line in mkvmerge_stdout.splitlines():
            if track_type in line:
                match = re.search(pattern, line)
                if match:
                    id_list.append(int(match.group(1)))
        return id_list

    @staticmethod
    def get_file_info(filepath, search_query):
        mkvinfo_stdout = CommandExecutor.get_stdout([str(Tools.mkvinfo), str(filepath)])
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
                        file_duration_timedelta = TypeConverter.str_to_timedelta(file_duration)
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
        return True if CommandExecutor.execute([str(tool), "-h"], exit_when_error=False) is None else False

    @classmethod
    def find_tool(cls, tool):
        potential_paths = [Path(tool)]

        if getattr(sys, 'frozen', False):
            tool_path_tale = f"tools/{tool}"
            if os.name == 'nt':
                tool_path_tale += '.exe'
            bundled_tool_path = Path(sys._MEIPASS) / tool_path_tale
            if bundled_tool_path.exists():
                potential_paths.insert(0, bundled_tool_path)

        if os.name == 'nt':  # Windows
            potential_paths.extend([
                Path.cwd() / f"{tool}.exe",
                Path(os.environ.get("PROGRAMFILES", "")) / "MkvToolNix" / f"{tool}.exe",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "MkvToolNix" / f"{tool}.exe",
                Path.home() / 'Downloads' / 'mkvtoolnix' / f"{tool}.exe"
            ])

        for path in potential_paths:
            if cls.available_tool(path):
                return path
        return None

    @classmethod
    def set_mkvtools_paths(cls):
        tools = {"mkvextract", "mkvinfo", "mkvmerge"}

        for tool in tools:
            setattr(cls, tool, cls.find_tool(tool))

        if None in [cls.mkvextract, cls.mkvinfo, cls.mkvmerge]:
            print("Error! MKVToolNix is not installed. Please install MKVToolNix "
                "and re-run the script:\nhttps://mkvtoolnix.download/downloads.html")
            sys.exit(1)

class Flags():
    def __init__(self):
        self.__flags = {
            "start_dir": None,
            "save_dir": None,
            "output_partname": "",
            "output_partname_tale": "",
            "limit_search_up": 3,
            "limit_generate": 99999,
            "range_generate": [0, 99999],
            "extended_log": False,
            "pro_mode": False,
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
            "sort_original_fonts": True,
            "add_tracknames": True,
            "for_priority": "file_first", #dir_first, mix
            "for": {"video": {},
                    "audio": {},
                    "subtitles": {},
                    "fonts": {},
                    }
            }

    types = {
        "path": {"start_dir", "save_dir"},
        "str": {"output_partname", "output_partname_tale", "trackname", "for_priority"},
        "num": {"limit_search_up", "limit_generate"},
        "range": {"range_generate"},
        "truefalse": {"extended_log", "pro_mode", "save_global_tags", "save_chapters", "save_audio",
                      "save_original_audio", "save_subtitles", "save_original_subtitles", "save_fonts",
                      "save_original_fonts", "sort_original_fonts", "add_tracknames", "save_files"
                      }
    }

    for_separate_flags = {"trackname", "save_files"}

    def set_flag(self, key, value, check_exists=True):
        if not check_exists or key in self.__flags:
            self.__flags[key] = value
        else:
            print(f"Error flag '{key}' not found, flag not set.")

    def flag(self, key, check_exists=True):
        value = self.__flags.get(key, None)
        if check_exists and value is None:
            print(f"Error flag '{key}' not found. Return None")
        return value

    def set_for_flag(self, key3, value):
        if key3 == "options":
            value = self.__flags["for"].get(self.for_key, {}).get("options", []) + value
        self.__flags["for"].setdefault(self.for_key, {})[key3] = value

    def for_flag(self, key2, key3):
        return self.__flags["for"].get(key2, {}).get(key3, None)

    def get_truefalse_by_arg(self, arg):
        self.value = not arg.startswith("--no")
        clean_arg = arg.replace("--no-", "save_").replace("--", "").replace("-", "_").replace("_attachments", "_fonts")
        clean_arg_alt = clean_arg.replace("save_", "")

        if clean_arg in Flags.types["truefalse"]:
            self.key = clean_arg
        elif clean_arg_alt in Flags.types["truefalse"]:
            self.key = clean_arg_alt

        else:
            return None
        return self.key

    def get_valueflag_by_arg(self, arg):
        self.value = None
        clean_arg = arg.replace("--", "")
        index = clean_arg.find("=")
        if index != -1:
            self.key = clean_arg[:index].replace("-", "_")
            value = clean_arg[index + 1:]
            number = TypeConverter.str_to_number(value)

            if self.key == "for":
                if self.for_key and self.for_key_options:
                    self.set_for_flag("options", self.for_key_options)

                str_value = value.strip("'\"")
                if str_value in {"all", ""}:
                    self.for_key = None
                else:
                    value = TypeConverter.str_to_path(str_value)
                    self.for_key = str(value)

                self.for_key_options = []
                return self.key

            elif self.key in Flags.types["path"]:
                self.value = TypeConverter.str_to_path(value.strip("'\""))

            elif self.key in Flags.types["str"]:
                self.value = value.strip("'\"")

            elif number is not None and self.key in Flags.types["num"]:
                self.value = number

            elif number is not None and self.key in Flags.types["range"]:
                num2 = self.__flags[self.key][1]
                self.value = [number, num2]

            elif self.key in Flags.types["range"]:
                match = re.search(r'[-:,]', value)
                if match:
                    index2 = match.start()

                    str_num1 = value[:index2]
                    str_num2 = value[index2 + 1:]
                    num1 = TypeConverter.str_to_number(str_num1)
                    num2 = TypeConverter.str_to_number(str_num2)

                    if num1 is not None and num2 is not None and num2 >= num1:
                        pass
                    elif num1 is not None:
                        num2 = self.__flags[self.key][1]
                    elif num2 is not None:
                        num1 = self.__flags[self.key][0]

                    if num1 is not None:
                        self.value = [num1, num2]

            if self.value is not None:
                return self.key

        return None

    def processing_sys_argv(self):
        pro_mode_setted = False
        self.for_key = None
        self.for_key_options = []

        if len(sys.argv) > 1:
            args = list(sys.argv[1:])
        else:
            args = []

        for arg in args:
            self.key = None
            self.value = None

            if self.for_key and not arg.startswith("--for="):
                if arg in Flags.for_separate_flags and self.get_truefalse_by_arg(arg) or self.get_valueflag_by_arg(arg):
                    self.set_for_flag(self.key, self.value)
                else:
                    self.for_key_options.append(arg.strip("'\""))
                continue

            elif not arg.startswith("--"):
                self.value = TypeConverter.str_to_path(arg.strip("'\""))
                if not self.flag("start_dir", check_exists=False):
                    self.key = "start_dir"
                elif not self.flag("save_dir", check_exists=False):
                    self.key = "save_dir"

            elif self.get_truefalse_by_arg(arg):
                pass

            elif self.get_valueflag_by_arg(arg):
                if self.key == "for":
                    continue

            if self.key and self.value is not None:
                self.set_flag(self.key, self.value)
            else:
                print(f"Unrecognized arg '{arg}'! \nExiting the script.")
                sys.exit(1)

            if self.key == "pro_mode":
                pro_mode_setted = True
            elif not pro_mode_setted and self.key not in {"start_dir", "save_dir"}:
                self.set_flag("pro_mode", True)
                pro_mode_setted = True

        if self.for_key and self.for_key_options:
            self.set_for_flag("options", self.for_key_options)

        if not self.flag("start_dir", check_exists=False):
            self.set_flag("start_dir", Path.cwd())
        if not self.flag("save_dir", check_exists=False):
            self.set_flag("save_dir", self.flag("start_dir"))

class FileDictionary:
    def __init__(self, flags):
        self.flags = flags
        self.video_list = []
        self.audio_dictionary = {}
        self.audio_trackname_dictionary = {}
        self.subtitles_dictionary = {}
        self.sub_trackname_dictionary = {}
        self.font_list = []
        self.create_file_list_set_dictionaries()

    EXTENSIONS = {
        'video': {'.mkv', '.m4v', '.mp4', '.avi', '.h264', '.hevc', '.ts', '.3gp',
                  '.flv', '.m2ts', '.mpeg', '.mpg', '.mov', '.ogm', '.webm', '.wmv'},

        'audio': {'.mka', '.m4a', '.aac', '.ac3', '.dts', '.dtshd', '.eac3', '.ec3', '.flac', '.mp2',
                  '.mpa', '.mp3', '.opus', '.truehd', '.wav', '.3gp', '.flv', '.m2ts', '.mkv', '.mp4',
                  '.avi', '.mpeg', '.mpg', '.mov', '.ts', '.ogg', '.ogm', '.webm', '.wmv'},

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

    @staticmethod
    def clean_tail(tail):
        execute = True
        while execute:
            if re.match(r'^\..{3}\..*$', tail):
                tail = tail[4:]
            else:
                execute = False

        for ext in FileDictionary.EXTENSIONS['video'].union(FileDictionary.EXTENSIONS['audio'], FileDictionary.EXTENSIONS['subtitles']):
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
    def remove_repeat_sort_fonts(font_list):
        stems = set()
        stem_list = []
        cleaned_list = []
        for font in font_list:
            if not font.stem in stems:
                stems.add(font.stem)
                stem_list.append(font.stem)

        stem_list.sort(key=str.lower)
        for stem in stem_list:
            for font in font_list:
                if font.stem == stem:
                    cleaned_list.append(font)
                    break
        return cleaned_list

    @staticmethod
    def find_subdirectories_by_string(base_dir):
        search_method = base_dir.glob('*')
        found_dir_list = []
        repeat_search = True
        while repeat_search:
            repeat_search = False
            for subdir in sorted(search_method, reverse=True):
                cln_subdir_name = re.sub(r"[ .]", "", subdir.name).lower()
                for key in FileDictionary.KEYS['search_subdir']:
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

        if any(key in search_str for key in FileDictionary.KEYS['skipdir_long']):
            return True

        while tail_path != tail_path.parent:
            tail_path = tail_path.parent
            search_str = tail_path.name.lower().replace(" ", "")
            if any(key == search_str for key in FileDictionary.KEYS['skipdir_short']):
                return True
        return False

    @classmethod
    def find_files_with_extensions(cls, search_dir, extensions, search_name="", recursive_search=False):
        if not search_dir.exists():
            return []
        search_method = search_dir.rglob('*') if recursive_search else search_dir.glob('*')
        found_files_list = []

        for filepath in sorted(search_method):
            if recursive_search and cls.path_contains_keyword(search_dir, filepath):
                continue

            filename = filepath.stem
            #если найденный файл содержит служебное имя пропускаем
            if any(key in filename for key in FileDictionary.KEYS['skip_file']):
                continue

            if (search_name in filename or filename in search_name) and filepath.is_file() and filepath.suffix.lower() in extensions:
                found_files_list.append(filepath)
        return found_files_list

    @classmethod
    def search_video_dir_upper(cls, flags, directory, extensions):
        filepath_list = cls.find_files_with_extensions(directory, extensions)
        for filepath in filepath_list:
            count = 0
            search_dir = directory
            while count <= flags.flag("limit_search_up"):
                video_list = cls.find_files_with_extensions(search_dir, FileDictionary.EXTENSIONS['video'], filepath.stem)
                for video in video_list:
                    #не выполняем если видео совпадает с файлом
                    if video == filepath:
                        continue
                    #проверяем что в видео есть видеодорожка, если нужно
                    if video.suffix not in FileDictionary.EXTENSIONS['container'] or video.parent != directory or FileInfo.file_has_video_track(video):
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
                if video.suffix not in FileDictionary.EXTENSIONS['container'] or video.parent != search_dir or FileInfo.file_has_video_track(video):
                    return found.parent
        return None

    @classmethod
    def search_subdir_when_adir_start_dir(cls, audio_dir, video_dir):
        recursive_search = False
        video_list = cls.find_files_with_extensions(video_dir, FileDictionary.EXTENSIONS['video'])
        if video_dir == audio_dir:
            subtitles_dir = cls.find_dir_with_filename_to_videoname(video_list, audio_dir, FileDictionary.EXTENSIONS['subtitles'], recursive_search)
            if subtitles_dir:
                return subtitles_dir
            else:
                return None

        search_dir_list = [audio_dir, video_dir]
        #поиск в стартовой директории и в видеодир без рекурсии
        for search_dir in search_dir_list:
            subtitles_dir = cls.find_dir_with_filename_to_videoname(video_list, search_dir, FileDictionary.EXTENSIONS['subtitles'], recursive_search)
            if subtitles_dir:
                return subtitles_dir

        #поиск в сабдиректориях по запросу с рекурсией
        search_dir_list = [video_dir] + cls.find_subdirectories_by_string(video_dir)
        for search_dir in reversed(search_dir_list):
            for recursive_search in [False, True]:
                subtitles_dir = cls.find_dir_with_filename_to_videoname(video_list, search_dir, FileDictionary.EXTENSIONS['subtitles'], recursive_search=recursive_search)
                if subtitles_dir:
                    return subtitles_dir
        return None

    @classmethod
    def find_font_directory(cls, subtitles_dir, video_dir):
        font_list = cls.find_files_with_extensions(subtitles_dir, FileDictionary.EXTENSIONS['font'], "", recursive_search=True)
        if font_list:
            return font_list[0].parent
        else:
            if subtitles_dir != video_dir:
                font_list = cls.find_files_with_extensions(subtitles_dir.parent, FileDictionary.EXTENSIONS['font'], "", recursive_search=True)
            if font_list:
                return font_list[0].parent
        return None

    @classmethod
    def collect_files_from_found_directories(cls, audio_dir, subtitles_dir, font_dir):
        audio_list = []
        subtitles_list = []
        font_list = []

        recursive_search=False
        if audio_dir:
            audio_list = cls.find_files_with_extensions(audio_dir, FileDictionary.EXTENSIONS['audio'], "", recursive_search)
        if subtitles_dir:
            subtitles_list = cls.find_files_with_extensions(subtitles_dir, FileDictionary.EXTENSIONS['subtitles'], "", recursive_search)
        if font_dir:
            font_list = cls.find_files_with_extensions(font_dir, FileDictionary.EXTENSIONS['font'], "", recursive_search)
        return audio_list, subtitles_list, font_list

    @classmethod
    def collect_files_from_start_dir(cls, search_dir):
        recursive_search = True
        audio_list = cls.find_files_with_extensions(search_dir, FileDictionary.EXTENSIONS['audio'], "", recursive_search)
        subtitles_list = cls.find_files_with_extensions(search_dir, FileDictionary.EXTENSIONS['subtitles'], "", recursive_search)
        font_list = cls.find_files_with_extensions(search_dir, FileDictionary.EXTENSIONS['font'], "", recursive_search)
        return audio_list, subtitles_list, font_list

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
            audio_trackname_dictionary[str(video)] = {}
            subtitles_dictionary[str(video)] = []
            sub_trackname_dictionary[str(video)] = {}

            for audio in audio_list:
                #если audio совпадает с video пропускаем audio или video
                if video == audio:
                    if found_video_track or FileInfo.file_has_video_track(video):
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
                    audio_trackname_dictionary[str(video)][str(audio)] = trackname
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
                    sub_trackname_dictionary[str(video)][str(subtitles)] = trackname
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
        self.video_dir = FileDictionary.search_video_dir_upper(self.flags, search_dir, FileDictionary.EXTENSIONS['audio'])
        if self.video_dir:
            self.flags.set_flag("video_dir_found", True)
            self.flags.set_flag("audio_dir_found", True)
            self.audio_dir = search_dir

            self.subtitles_dir = FileDictionary.search_subdir_when_adir_start_dir(self.audio_dir, self.video_dir)
            if self.subtitles_dir:
                self.flags.set_flag("subtitles_dir_found", True)

        else: # Поиск видеодиректории через сабы
            self.video_dir = FileDictionary.search_video_dir_upper(self.flags, search_dir, FileDictionary.EXTENSIONS['subtitles'])
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
        video_list = FileDictionary.find_files_with_extensions(search_dir, FileDictionary.EXTENSIONS['video'])
        if not video_list:
            self.video_list = []
            return

        if self.flags.flag("audio_dir_found") or self.flags.flag("subtitles_dir_found"):
            audio_list, subtitles_list, self.font_list = FileDictionary.collect_files_from_found_directories(self.audio_dir, self.subtitles_dir, self.font_dir)

        else:
            audio_list, subtitles_list, font_list = FileDictionary.collect_files_from_start_dir(self.flags.flag("start_dir"))
            if font_list:
                self.font_list = FileDictionary.remove_repeat_sort_fonts(font_list)

        self.video_list, self.audio_dictionary, self.audio_trackname_dictionary, self.subtitles_dictionary, self.sub_trackname_dictionary = FileDictionary.create_dictionaries(video_list, audio_list, subtitles_list)

        if not self.video_list: #пробуем найти mkv для обработки линковки
            self.audio_dictionary = self.audio_trackname_dictionary = self.subtitles_dictionary = self.sub_trackname_dictionary = self.font_list = {}
            self.video_list = FileDictionary.find_files_with_extensions(self.flags.flag("start_dir"), ".mkv")

class Merge(FileDictionary):
    def set_output_path(self, tail=""):
        if self.output_partname or self.output_partname_tale:
            name = f"{self.output_partname}{self.current_index+1:0{len(str(self.video_list_length))}d}{self.output_partname_tale}"
            self.output = Path(self.flags.flag("save_dir")) / f"{name}.mkv"

        else:
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

            if self.font_list and self.flags.flag("save_fonts"):
                if self.flags.flag("save_original_fonts"):
                    partname = partname + "_added_fonts"
                else:
                    partname = partname + "_replaced_fonts"

            self.output = Path(self.flags.flag("save_dir")) / f"{partname}.mkv"

    def get_part_command_for_video(self):
        part_command = []
        empty_no_attachments_arg = not self.orig_font_list or (self.flags.flag("save_original_fonts") and not self.flags.flag("sort_original_fonts"))

        if not empty_no_attachments_arg:
            part_command.append("--no-attachments")
        if not self.flags.flag("save_global_tags"):
            part_command.append("--no-global-tags")
        if not self.flags.flag("save_chapters"):
            part_command.append("--no-chapters")
        if not self.flags.flag("save_original_audio"):
            part_command.append("--no-audio")
        if not self.flags.flag("save_original_subtitles"):
            part_command.append("--no-subtitles")
        if self.video_options:
            part_command.extend(self.video.options)

        return part_command

    def get_part_command_for_file(self, filepath, filegroup, tracknames={}, add_trackname=True):
        part_command = []
        keys2 = []

        if self.mkv_has_segment_linking:
            keys2.append(self.matching_keys.get(str(filepath), str(filepath)))
            keys2.append(filegroup)
            keys2.append(self.matching_keys.get(str(filepath.parent), str(filepath.parent)))
        else:
            keys2 = [str(filepath), filegroup, str(filepath.parent)]

        if self.get_for_merge_flag(keys2, "save_files") is False:
            return []

        options = self.get_for_merge_flag(keys2, "options")
        if options:
            part_command.extend(options)

        if add_trackname:
            forced_trackname = self.get_for_merge_flag(keys2, "trackname")
            trackname = forced_trackname if forced_trackname else tracknames.get(str(filepath), "")
            if forced_trackname or (trackname and not (filepath.suffix in {".mka", ".mkv", ".mks"} and FileInfo.get_file_info(filepath, "Name:"))):
                track_id_list = FileInfo.get_track_type_id(filepath, filegroup)
                for track_id in track_id_list:
                    part_command.extend(["--track-name", f"{track_id}:{trackname}"])

        part_command.append(str(filepath))
        return part_command

    def get_merge_command(self):
        command = [str(Tools.mkvmerge), "-o", str(self.output)]

        part_command = self.get_part_command_for_video()
        command.extend(part_command + [str(self.merge_video_list[0])])
        for video in self.merge_video_list[1:]:
            command.extend(part_command + [f"+{str(video)}"])

        for audio in self.audio_list:
            part_command = self.get_part_command_for_file(audio, "audio", self.audio_tracknames)
            if part_command:
                command.extend(part_command)

        for sub in self.subtitles_list:
            part_command = self.get_part_command_for_file(sub, "subtitles", self.subs_tracknames)
            if part_command:
                for_id = self.set_cp1251_for_subs.get(str(sub), None)
                if for_id:
                    command.extend(["--sub-charset", f"{for_id}:windows-1251"])
                command.extend(part_command)

        for font in self.merge_font_list:
            part_command = self.get_part_command_for_file(font, "fonts", add_trackname=False)
            if part_command:
                part_command.insert(len(part_command) - 1, "--attach-file")
                command.extend(part_command)

        return command

    def processing_error_warning_merge(self, command_out, lmsg):
        cleaned_out = ''.join(command_out.split()).lower()
        last_line_out = command_out.splitlines()[-1]
        cleaned_lline_out = ''.join(last_line_out.split()).lower()

        if not self.has_coding_cp1251 and "textsubtitletrackcontainsinvalid8-bitcharacters" in cleaned_out:
            print("Invalid 8-bit characters in subtitles file!")
            for line in command_out.splitlines():
                if line.startswith("Warning") and "invalid 8-bit characters" in line:
                    filename_match = re.search(r"'(/[^']+)'", line)
                    filename = filename_match.group(1) if filename_match else None
                    filepath = TypeConverter.str_to_path(filename)

                    track_id_match = re.search(r"track (\d+)", line)
                    track_id = track_id_match.group(1) if track_id_match else None
                    if filename and track_id:
                        self.set_cp1251_for_subs[str(filepath)] = track_id
                        self.has_coding_cp1251 = True

            if self.has_coding_cp1251:
                print("Trying to generate with windows-1251 coding.")
                self.execute_merge()
                self.set_cp1251_for_subs = {}
                self.has_coding_cp1251 = False
                return

        if not cleaned_lline_out.startswith("error"):
            print(lmsg)

            if "thecodec'sprivatedatadoesnotmatch" in cleaned_out:
                print(f"Attention! The video file maybe corrupted because video parts have mismatched codec parameters. Please check the video file.")

        else:
            if "containschapterswhoseformatwasnotrecognized" in cleaned_lline_out:
                print(f"{last_line_out}\nTrying to generate without chapters.")
                self.flags.set_flag("save_chapters", False)
                self.execute_merge()
                self.flags.set_flag("save_chapters", True)

            elif "nospaceleft" in cleaned_lline_out:
                if self.output.exists():
                    self.output.unlink()
                self.delete_temp_files()
                print(f"Error writing file!\nPlease re-run the script with a different save directory.\nExiting the script.")
                sys.exit(1)

            else:
                if self.output.exists():
                    self.output.unlink()
                self.delete_temp_files()
                print(f"Error executing the command!\n{last_line_out}\nExiting the script.")
                sys.exit(1)

    def execute_merge(self):
        command = self.get_merge_command()

        print(f"\nGenerating a merged video file using mkvmerge. Executing the command: \n{TypeConverter.command_to_print_str(command)}")
        lmsg = f"The command was executed successfully. The generated video file was saved to:\n{str(self.output)}"

        command_out = CommandExecutor.get_stdout(command, exit_when_error=False)
        if self.flags.flag("extended_log"):
            print(command_out)

        if not isinstance(command_out, tuple):
            print(lmsg)
        else:
            command_out = command_out[0]
            self.processing_error_warning_merge(command_out, lmsg)

    def set_merge_flags(self):
        save_original_audio = not self.flags.flag("audio_dir_found") or not self.audio_list
        self.flags.set_flag("save_original_audio", save_original_audio)

        save_original_subtitles = not self.flags.flag("subtitles_dir_found") or not self.subtitles_list
        self.flags.set_flag("save_original_subtitles", save_original_subtitles)

        save_fonts = True if self.subtitles_list else False
        self.flags.set_flag("save_fonts", save_fonts)

    def extract_original_fonts(self):
        if self.orig_font_dir.exists():
            shutil.rmtree(self.orig_font_dir)
        self.orig_font_dir.mkdir(parents=True)
        self.orig_font_list = []

        for video in self.merge_video_list:
            name_list = []
            command = [str(Tools.mkvmerge), "-i", str(video)]
            stdout = CommandExecutor.get_stdout(command)
            for line in stdout.splitlines():
                match = re.search(r"file name '(.+?)'", line)
                if match:
                    name = match.group(1)
                    name_list.append(name)

            count = 1
            command = [str(Tools.mkvextract), str(video), "attachments"]
            for name in name_list:
                filepath = Path(self.orig_font_dir) / name
                command.append(f"{count}:{filepath}")
                count += 1
            if count > 1:
                CommandExecutor.execute(command)

        self.orig_font_list = FileDictionary.find_files_with_extensions(self.orig_font_dir, FileDictionary.EXTENSIONS["font"])

    def delete_temp_files(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def get_for_merge_flag(self, keys2, key3):
        flag = None
        flag_list = []

        if self.for_priority == "dir_first":
            for key2 in reversed(keys2):
                flag = self.flags.for_flag(key2, key3)
                if flag is not None:
                    break

        else:
            for key2 in keys2:
                if self.for_priority == "mix":
                    flag_list.append(self.flags.for_flag(key2, key3))
                else:
                    flag = self.flags.for_flag(key2, key3)
                    if flag is not None:
                        break

            if len(flag_list) > 0:

                if key3 == "options":
                    flag = []
                    for flg in flag_list:
                        if flg:
                            flag += flg

                elif key3 in Flags.types["truefalse"]:
                    flag = not False in flag_list

                elif key3 in Flags.types["str"]:
                    flag = ""
                    for flg in flag_list:
                        if flg:
                            flag += flg

        return flag

    def set_merge_vars(self):
        self.video_list_length = len(self.video_list)
        self.add_tracknames = self.flags.flag("add_tracknames")
        self.output_partname = self.flags.flag("output_partname")
        self.output_partname_tale = self.flags.flag("output_partname_tale")
        self.linked_uid_info_dict = {}
        self.temp_dir = Path(self.flags.flag("save_dir")) / f"__temp_files__{str(uuid.uuid4())[:8]}"
        self.orig_font_list = []
        self.orig_font_dir = Path(self.temp_dir) / "orig_fonts"
        self.for_priority = self.flags.flag("for_priority")
        self.has_coding_cp1251 = False
        self.set_cp1251_for_subs = {}

        self.limit_generate = self.flags.flag("limit_generate")
        self.count_generated = 0
        self.count_gen_before = 0

        self.start_range = self.flags.flag("range_generate")[0]
        self.end_range = self.flags.flag("range_generate")[1]
        if self.start_range > 0:
            self.start_range = self.start_range - 1
            self.end_range = self.end_range - 1

        self.current_index = self.start_range

    def merge_all_files(self):
        self.set_merge_vars()

        for self.video in self.video_list[self.start_range:]:
            self.mkv_has_segment_linking = False

            if self.count_generated >= self.limit_generate or self.current_index > self.end_range:
                break

            video_keys2 = [str(self.video), "video", str(self.video.parent)]
            if self.get_for_merge_flag(video_keys2, "save_files") is False:
                self.current_index += 1
                continue
            self.video_options = self.get_for_merge_flag(video_keys2, "options")

            self.merge_video_list = [self.video]

            if self.flags.flag("save_audio"):
                self.audio_list = self.audio_dictionary.get(str(self.video), [])
                self.audio_tracknames = self.audio_trackname_dictionary.get(str(self.video), {}) if self.add_tracknames else {}
            else:
                self.audio_list = []
                self.audio_tracknames = {}

            if self.flags.flag("save_subtitles"):
                self.subtitles_list = self.subtitles_dictionary.get(str(self.video), [])
                self.subs_tracknames = self.sub_trackname_dictionary.get(str(self.video), {}) if self.add_tracknames else {}
            else:
                self.subtitles_list = []
                self.subs_tracknames = {}

            self.merge_font_list = self.font_list if self.flags.flag("save_fonts") else []

            if not self.flags.flag("pro_mode"):
                self.set_merge_flags()

            self.set_output_path()
            if self.video.suffix == ".mkv":
                linked = LinkedMKV(self)

                if linked.mkv_has_segment_linking():
                    self.mkv_has_segment_linking = True
                    self.set_output_path("_merged_video")

                else:
                    if not self.audio_list and not self.subtitles_list and not self.font_list:
                        self.current_index += 1
                        continue #пропускаем если нет ни линковки ни аудио ни сабов ни шрифтов

            if self.output.exists():
                self.count_gen_before += 1
                self.current_index += 1
                continue

            if self.mkv_has_segment_linking:
                linked.processing_linked_mkv()
                self.matching_keys = linked.matching_keys

            if self.flags.flag("sort_original_fonts") and self.flags.flag("save_original_fonts"):
                self.extract_original_fonts()
                if self.orig_font_list and self.merge_font_list:
                    self.merge_font_list = FileDictionary.remove_repeat_sort_fonts(self.merge_font_list + self.orig_font_list)
                elif self.orig_font_list:
                    self.merge_font_list = self.orig_font_list

            self.execute_merge()
            self.count_generated += 1
            self.current_index += 1

        self.delete_temp_files()

class LinkedMKV:
    def __init__(self, merge_instance):
        self.merge = merge_instance

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
            defacto_start = TypeConverter.str_to_timedelta(timestamps[0])
            defacto_end = TypeConverter.str_to_timedelta(timestamps[1])
            offset_start = defacto_start - split_start
            offset_end = defacto_end - split_end
        elif len(timestamps) == 1:
            timestamp = TypeConverter.str_to_timedelta(timestamps[0])
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
        CommandExecutor.execute(command)

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
        mkvmerge_stdout = CommandExecutor.get_stdout(command)
        segment, defacto_start, defacto_end, offset_start, offset_end = LinkedMKV.get_segment_info(mkvmerge_stdout, partname, start, end)
        length = defacto_end - defacto_start

        return segment, length, offset_start, offset_end

    @staticmethod
    def merge_file_segments(segment_list, output):
        command = [str(Tools.mkvmerge), "-o", str(output)]
        command.append(segment_list[0])
        for segment in segment_list[1:]:
            command.append(f"+{str(segment)}")
        CommandExecutor.execute(command)

    def extract_chapters(self):
        command = [str(Tools.mkvextract), str(self.merge.video), "chapters", str(self.chapters)]
        CommandExecutor.execute(command)

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
            chapter_start = TypeConverter.str_to_timedelta(chapter_start.text) if chapter_start is not None else None
            self.start_list.append(chapter_start)

            chapter_end = chapter_atom.find("ChapterTimeEnd")
            chapter_end = TypeConverter.str_to_timedelta(chapter_end.text) if chapter_end is not None else None
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
                            temp_video = LinkedMKV.find_video_with_uid(self.merge.video.parent, uid)
                            if not temp_video:
                                print(f"Video file with uid {uid} not found in the video directory '{str(self.merge.video.parent)}'\nThis file is part of the linked video '{str(self.merge.video)}' and is required for merging. Please move this file to the video directory and re-run the script.")
                                sys.exit(1)
                        else:
                            temp_video = self.merge.video
                        temp_end = FileInfo.get_file_info(temp_video, "Duration")

                temp_start_list.append(temp_start)
                temp_end_list.append(temp_end)
                if not uid:
                    prev_nonid_end = temp_end
                count += 1
            self.start_list = temp_start_list
            self.end_list = temp_end_list

    def read_uid_file_info(self):
        self.segment = None
        self.length = None
        self.offset_start = None
        self.offset_end = None

        info_list = self.merge.linked_uid_info_dict.get(f"{self.uid}", None)
        if info_list and len(info_list) == 6:
            self.to_split = info_list[0]
            #если время предыдущего сплита этого uid совпадает
            if info_list[1] == self.start and (info_list[2] == self.end or info_list[3] <= self.end):
                #и нужный сплит существует не сплитуем
                self.segment = Path(self.merge.temp_dir) / f"segment_video_{self.uid}.mkv"
                if self.segment.exists():
                    self.length = info_list[3]
                    self.offset_start = info_list[4]
                    self.offset_end = info_list[5]
                    self.execute_split = False

        else:
            self.to_split = LinkedMKV.find_video_with_uid(self.video_dir, self.uid)

    def get_segment_linked_video(self):
        self.execute_split = True
        self.prev_offset_end = self.offset_end
        self.chapter_start = self.start
        self.chapter_end = self.end

        if self.uid:
            self.read_uid_file_info()
        else:
            self.to_split = self.merge.video
            self.start = self.prev_nonuid_end

        if self.execute_split:
            self.prev_lengths = self.lengths
            self.segment, length, self.offset_start, self.offset_end = LinkedMKV.split_file(self.to_split, self.partname, self.start, self.end, save_original_fonts=self.merge.flags.flag("save_original_fonts"))
            self.lengths = self.lengths + length

            if self.uid: # сплит по внешнему файлу переименовываем чтоб использовать дальше
                new_path = Path(self.merge.temp_dir) / f"segment_video_{self.uid}.mkv"
                if new_path.exists():
                    new_path.unlink()
                self.segment.rename(new_path)
                self.segment = new_path

                length = self.lengths - self.prev_lengths
                self.merge.linked_uid_info_dict[f"{self.uid}"] = [self.to_split, self.start, self.end, length, self.offset_start, self.offset_end]

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

        self.video_dir = self.merge.video.parent
        self.lengths = timedelta(0)
        self.offset_start = timedelta(0)
        self.offset_end = timedelta(0)
        self.prev_nonuid_end = timedelta(0)
        count = 0
        for self.uid in self.uid_list:
            self.start = self.start_list[count]
            self.end = self.end_list[count]
            self.partname = Path(self.merge.temp_dir) / f"segment_video_{count}.mkv"
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

            if source == self.merge.video:
                start = prev_lengths - uid_lengths + offset_lengths if prev_lengths - uid_lengths + offset_lengths > timedelta(0) else timedelta(0)
                end = lengths - uid_lengths
            else:
                start = offset_lengths if offset_lengths > timedelta(0) else timedelta(0)
                end = start + length - offset_lengths if start != timedelta(0) else length
                uid_lengths = uid_lengths + length

            partname = Path(self.temp_orig_audio_dir) / f"{count}.mka"
            a_segment, a_length, offset_start, offset_end = LinkedMKV.split_file(source, partname, start, end, file_type="audio", track_id=self.track_id)
            if offset_start > timedelta(milliseconds=200) or offset_end > timedelta(milliseconds=200):
                new_start = start - offset_start if start - offset_start > timedelta(0) else start
                new_end = end - offset_end
                a_segment, a_length, offset_start, offset_end = LinkedMKV.split_file(source, partname, new_start, new_end, file_type="audio", track_id=self.track_id)

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

            if self.source_list[count] == self.merge.video:
                start = prev_lengths + offset_audio_to_video

                if offset_end > timedelta(milliseconds=2000) and len(self.source_list) > count+2 and self.merge.video == self.source_list[count+2]:
                    end = lengths - offset_end
                    compensation_start = self.lengths_list[count+1] - self.offset_start_list[count+2]
                    add_compensation = True
                else:
                    end = lengths
            else:
                start = prev_lengths - offset_start + offset_audio_to_video
                end = start + length

            partname = Path(self.retimed_audio.parent) / f"{count}.mka"
            a_segment, a_length, split_offset_start, split_offset_end = LinkedMKV.split_file(self.audio, partname, start, end, file_type="audio")

            if split_offset_start > timedelta(milliseconds=200) or split_offset_end > timedelta(milliseconds=200):
                new_start = start - split_offset_start if start - split_offset_start > timedelta(0) else start
                new_end = end - split_offset_end
                a_segment, a_length, *_ = LinkedMKV.split_file(self.audio, partname, new_start, new_end, file_type="audio")

            if add_compensation:
                compensation_length = length - a_length
                if compensation_length > timedelta(milliseconds=500):
                    partname = Path(self.retimed_audio.parent) / f"compensation_{count}.mka"
                    compensation_end = compensation_start + compensation_length
                    compensation_segment, compensation_length, *_ = LinkedMKV.split_file(self.audio, partname, compensation_start, compensation_end, file_type="audio")
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
        if self.merge.flags.flag("save_original_audio"):
            audio_track_id_list = FileInfo.get_track_type_id(self.merge.video, "audio")
            for self.track_id in audio_track_id_list:
                self.get_retimed_segments_orig_audio()
                orig_audio = Path(self.temp_orig_audio_dir) / f"{count}.mka"
                LinkedMKV.merge_file_segments(self.a_segment_list, orig_audio)

                self.retimed_audio_list.append(orig_audio)
                count += 1

        for self.audio in self.merge.audio_list:
            self.retimed_audio = Path(self.temp_ext_audio_dir) / self.audio.parent.name / f"{count}.mka"
            self.get_retimed_segments_ext_audio()
            LinkedMKV.merge_file_segments(self.a_segment_list, self.retimed_audio)

            self.retimed_audio_list.append(self.retimed_audio)
            self.set_matching_keys(self.audio, self.retimed_audio)

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

                if self.source_list[count] == self.merge.video:
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
                        dialogue_time_start = TypeConverter.str_to_timedelta(str_dialogue_time_start)
                        dialogue_time_end = TypeConverter.str_to_timedelta(str_dialogue_time_end)

                        #не включаем строки не входящие в сегмент
                        if dialogue_time_start < remove_border_start and dialogue_time_end < remove_border_start:
                            continue
                        elif dialogue_time_start > remove_border_end and dialogue_time_end > remove_border_end:
                            continue

                        else: #ретаймим и записываем
                            new_dialogue_time_start = dialogue_time_start + retime_offset
                            new_dialogue_time_end = dialogue_time_end + retime_offset
                            str_new_dialogue_time_start = TypeConverter.timedelta_to_str(new_dialogue_time_start)
                            str_new_dialogue_time_end = TypeConverter.timedelta_to_str(new_dialogue_time_end)
                            line = f"{parts[0]},{str_new_dialogue_time_start},{str_new_dialogue_time_end},{','.join(parts[3:])}"
                            file.write(line)

                prev_lengths = lengths
                prev_offset_end = offset_end
                if self.source_list[count] == self.merge.video:
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
                if self.merge.video == self.source_list[count]: #если отрезок из основного файла
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
                        dialogue_time_start = TypeConverter.str_to_timedelta(str_dialogue_time_start)
                        dialogue_time_end = TypeConverter.str_to_timedelta(str_dialogue_time_end)

                        #не включаем строки не входящие в сегмент
                        if dialogue_time_start < remove_border_start and dialogue_time_end < remove_border_start:
                            continue
                        elif dialogue_time_start > remove_border_end and dialogue_time_end > remove_border_end:
                            continue

                        else: #ретаймим и записываем
                            new_dialogue_time_start = dialogue_time_start + retime_offset
                            new_dialogue_time_end = dialogue_time_end + retime_offset
                            str_new_dialogue_time_start = TypeConverter.timedelta_to_str(new_dialogue_time_start)
                            str_new_dialogue_time_end = TypeConverter.timedelta_to_str(new_dialogue_time_end)
                            line = f"{parts[0]},{str_new_dialogue_time_start},{str_new_dialogue_time_end},{','.join(parts[3:])}"
                            file.write(line)
                prev_lengths = lengths
                prev_offset_end = offset_end
                count += 1

    def get_retimed_sub_list(self):
        count = 0
        self.retimed_sub_list = []

        if self.merge.flags.flag("save_original_subtitles"):
            self.segment_orig_sub_list = []

            #проверяем сколько дорожек субтитров в исходном видео
            sub_track_id_list = FileInfo.get_track_type_id(self.merge.video, "subtitles")
            for self.track_id in sub_track_id_list:
                count_temp = 0
                for source in self.source_list:
                    split_original_sub = Path(self.temp_orig_subs_dir) / f"{count + count_temp}.ass"
                    LinkedMKV.extract_track(source, split_original_sub, self.track_id)
                    self.segment_orig_sub_list.append(split_original_sub)
                    count_temp += 1

                self.retime_original_sub()
                self.retimed_sub_list.append(self.retimed_original_sub)
                count += 1

        for subs in self.merge.subtitles_list:
            self.sub_for_retime = Path(self.temp_ext_subs_dir) / subs.parent.name / f"{count}.ass"
            if subs.suffix != ".ass":
                print(f"\nSkip subtitles! {str(subs)} \nThese subtitles need to be retimed because the video file has segment linking. Retime is only possible for .ass subtitles.")
                continue
            else:
                self.sub_for_retime.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(subs, self.sub_for_retime)

            self.retime_external_sub()
            self.retimed_sub_list.append(self.retimed_external_sub)
            self.set_matching_keys(subs, self.retimed_external_sub)

            count += 1

    def set_linked_temp_dirs(self):
        self.temp_orig_audio_dir = Path(self.merge.temp_dir) / "orig_audio"
        self.temp_orig_audio_dir.mkdir(parents=True, exist_ok=True)
        self.temp_ext_audio_dir = Path(self.merge.temp_dir) / "ext_audio"
        self.temp_ext_audio_dir.mkdir(parents=True, exist_ok=True)

        self.temp_orig_subs_dir = Path(self.merge.temp_dir) / "orig_subs"
        self.temp_orig_subs_dir.mkdir(parents=True, exist_ok=True)
        self.temp_ext_subs_dir = Path(self.merge.temp_dir) / "ext_subs"
        self.temp_ext_subs_dir.mkdir(parents=True, exist_ok=True)

    def set_matching_keys(self, old_filepath, new_filepath):
        old_keys2 = [str(old_filepath), str(old_filepath.parent)]
        new_keys2 = [str(new_filepath), str(new_filepath.parent)]
        keys3 = Flags.for_separate_flags.union({"options"})

        count = 0
        for old_key2 in old_keys2:
            if old_key2 in self.merge.audio_tracknames or self.merge.subs_tracknames:
                self.matching_keys[new_keys2[count]] = old_key2
                count += 1
                continue

            for key3 in keys3:
                value = self.merge.for_flag(old_key2, key3)
                if value is not None:
                    self.matching_keys[new_keys2[count]] = old_key2
                    break

            count += 1

    def processing_linked_mkv(self):
        self.matching_keys = {}
        if not hasattr(self, 'temp_orig_audio_dir'):
            self.set_linked_temp_dirs()

        self.get_all_segments_linked_video()
        self.merge.merge_video_list = self.segment_list

        self.get_retimed_audio_list()
        self.merge.audio_list = self.retimed_audio_list

        self.get_retimed_sub_list()
        self.merge.subtitles_list = self.retimed_sub_list

    def mkv_has_segment_linking(self):
        self.chapters = Path(self.merge.temp_dir) / "chapters.xml"
        if self.chapters.exists():
            self.chapters.unlink()
        self.extract_chapters()
        if not self.chapters.exists():
            return False

        self.get_chapters_info()
        return True if self.uid_list else False

def main():
    flags = Flags()
    flags.processing_sys_argv()
    if flags.flag("limit_generate") == 0:
        print("A new video can't be generated because the limit-generate set to 0. \nExiting the script.")
        sys.exit(0)

    Tools.set_mkvtools_paths()

    print(f"\nTrying to generate a new video in the save directory '{str(flags.flag("save_dir"))}' using files from the start directory '{str(flags.flag("start_dir"))}'.")
    lmsg = f"Files for generating a new video not found. Checked the directory '{str(flags.flag("start_dir"))}', its subdirectories and {flags.flag("limit_search_up")} directories up."

    merge = Merge(flags)
    if not merge.video_list:
        print(lmsg)
        sys.exit(0)
    if merge.flags.flag("range_generate")[0] > len(merge.video_list):
        print(f"A new video can't be generated because the start range-generate exceeds the number of video files. \nExiting the script.")
        sys.exit(0)
    merge.merge_all_files()

    if merge.count_gen_before:
        print(f"{merge.count_gen_before} video files in the save directory '{str(flags.flag("save_dir"))}' had generated names before the current run of the script. Generation for these files has been skipped.")

    if merge.count_generated:
        print(f"\nThe script was executed successfully. {merge.count_generated} video files were generated in the directory '{str(flags.flag("save_dir"))}'")
    else:
        print(lmsg)

if __name__ == "__main__":
    main()
