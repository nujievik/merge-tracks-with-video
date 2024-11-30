"""
generate-video-with-these-files-v0.5.7
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
    def get_track_type_tids(filepath, track_type):
        id_list = []
        track_type = track_type if track_type != "subs" else "subtitles"
        pattern = r"Track ID (\d+):"
        mkvmerge_stdout = CommandExecutor.get_stdout([str(Tools.mkvmerge), "-i", str(filepath)])
        for line in mkvmerge_stdout.splitlines():
            if track_type in line:
                match = re.search(pattern, line)
                if match:
                    id_list.append(int(match.group(1)))
        return id_list

    @staticmethod
    def get_file_info(filepath, query):
        if filepath.suffix not in FileDictionary.EXTENSIONS['mkvinfo_supported']:
            return
        mkvinfo_stdout = CommandExecutor.get_stdout([str(Tools.mkvinfo), str(filepath)])
        for line in mkvinfo_stdout.splitlines():
            if query in line:
                if "Segment UID:" in query:
                    uid_hex = line.strip()
                    # Преобразуем в строку формата 93828424aeb8a27a942fb070d17459f8
                    uid_clean = "".join(byte[2:] for byte in uid_hex.split() if byte.startswith("0x"))
                    return uid_clean

                if "Duration:" in query:
                    match = re.search(rf"{query}\s*(.*)", line)  # Находим всю часть после 'Duration:'
                    if match:
                        file_duration = match.group(1).strip()  # Убираем пробелы
                        file_duration_timedelta = TypeConverter.str_to_timedelta(file_duration)
                        return file_duration_timedelta

                if "Name:" in query:
                    return True

                if "Language:" in query:
                    match = re.search(rf"{query}\s*(.*)", line)
                    if match:
                        lang = match.group(1).strip()
                        return lang if lang != "und" else None

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
            tool_path_tail = f"tools/{tool}"
            if os.name == 'nt':
                tool_path_tail += '.exe'
            bundled_tool_path = Path(sys._MEIPASS) / tool_path_tail
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
        self.__flags = {}

    DEFAULT = {
        "start_dir": Path.cwd(),
        "save_dir": Path.cwd(),
        'locale': 'rus',
        "out_pname": "",
        "out_pname_tail": "",
        "lim_search_up": 3,
        "lim_gen": 99999,
        'lim_default_ttype': 1,
        'lim_forced_signs': 1,
        "range_gen": [0, 99999],
        "pro": False,
        "extended_log": False,
        "global_tags": True,
        "chapters": True,
        "video": True,
        "audio": True,
        "orig_audio": True,
        "subs": True,
        "orig_subs": True,
        "fonts": True,
        "orig_fonts": True,
        "sort_orig_fonts": True,
        "tracknames": True,
        "langs": True,
        'enableds': True, 'enabled': True,
        'defaults': True, 'default': True,
        'forceds': True, 'forced': False, 'forced_signs': False,
        't_orders': True,
        'for_priority': 'file_first', #dir_first, mix
        'for': {}
    }

    MATCHINGS_PART = {
        'pro_mode': 'pro',
        'directory': 'dir',
        'output': 'out',
        'partname': 'pname',
        'limit': 'lim',
        'generate': 'gen',
        'save_': '',
        'no_': '',
        'add_': '',
        '-': '_',
        'original': 'orig',
        'subtitles': 'subs',
        'attachments': 'fonts',
        'language': 'lang',
        'track_enabled_flag': 'enabled',
        'default_track_flag': 'default',
        'forced_display_flag': 'forced',
        'track_orders': 't_orders',
    }

    TYPES = {
        "path": {"start_dir", "save_dir"},
        "str": {"out_pname", "out_pname_tail", "trackname", "for_priority", "lang", "locale"},
        'num': {'lim_search_up', 'lim_gen', 'lim_forced_signs'},
        "range": {"range_gen"},
        'truefalse': {'pro', 'extended_log', 'global_tags', 'chapters', 'video', 'audio',
                      'orig_audio', 'subs', 'orig_subs', 'fonts', 'orig_fonts', 'sort_orig_fonts',
                      'langs', 'tracknames', 'files', 'enableds', 'enabled', 'defaults', 'default',
                      'forceds', 'forced', 'forced_signs', 't_orders',
                      }
    }

    FOR_SEPARATE_FLAGS = (TYPES['truefalse']).union({'trackname', 'lang'}) - {'extended_log'}

    def set_flag(self, key, value, check_exists=False):
        if not check_exists or key in self.__flags:
            self.__flags[key] = value
        else:
            print(f"Error flag '{key}' not found, flag not set.")

    def flag(self, key, default_if_missing=True):
        value = self.__flags.get(key, None)
        if value is None and default_if_missing:
            value = __class__.DEFAULT.get(key, None)
        return value

    def set_for_flag(self, key3, value):
        if key3 == 'options':
            value = self.__flags.get('for', {}).get(self.for_key, {}).get('options', []) + value
        self.__flags.setdefault('for', {}).setdefault(self.for_key, {})[key3] = value

    def for_flag(self, key2, key3):
        return self.__flags.get('for', {}).get(key2, {}).get(key3, None)

    def set_key_by_arg(self, arg):
        self.key = None

        if not arg.startswith(("-", "+")):
            if str(self.flag("start_dir")) == str(Path.cwd()):
                self.key = "start_dir"
            elif str(self.flag("save_dir")) == str(Path.cwd()):
                self.key = "save_dir"
            return

        clean_arg = arg.strip("'\"").lstrip("-+")
        index = clean_arg.find("=")
        if index != -1:
            self.key = clean_arg[:index]
        else:
            self.key = clean_arg

        repeat = True
        while repeat:
            repeat = False
            for find, replace in Flags.MATCHINGS_PART.items():
                if find in self.key:
                    self.key = self.key.replace(find, replace)
                    repeat = True

    def get_truefalse_by_arg(self, arg):
        if self.key in Flags.TYPES['truefalse']:
            self.value = not (arg.startswith("--no") or (arg.startswith("-") and not arg.startswith("--")))
        return self.value

    def get_valueflag_by_arg(self, arg):
        index = arg.find("=")
        if index != -1:
            value = arg[index + 1:]
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

            elif self.key in Flags.TYPES["path"]:
                self.value = TypeConverter.str_to_path(value.strip("'\""))

            elif f"save_{self.key}" in Flags.TYPES["path"]:
                self.key = f"save_{self.key}"
                self.value = TypeConverter.str_to_path(value.strip("'\""))

            elif self.key in Flags.TYPES["str"]:
                self.value = value.strip("'\"")

            elif number is not None and self.key in Flags.TYPES["num"]:
                self.value = number

            elif number is not None and self.key in Flags.TYPES["range"]:
                num2 = self.__flags[self.key][1]
                self.value = [number, num2]

            elif self.key in Flags.TYPES["range"]:
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

        return self.value

    def set_value_by_arg(self, arg):
        self.value = None
        if not arg.startswith(("-", "+")):
            self.value = TypeConverter.str_to_path(arg.strip("'\""))
        elif self.get_truefalse_by_arg(arg):
            pass
        elif self.get_valueflag_by_arg(arg):
            pass

    def processing_for_arg(self, arg):
        if self.key == 'for':
            return True

        elif self.for_key:
            if self.key in Flags.FOR_SEPARATE_FLAGS and self.value is not None:
                self.set_for_flag(self.key, self.value)
            else:
                self.for_key_options.append(arg.strip("'\""))
            return True

    def processing_sys_argv(self):
        self.for_key = None
        self.for_key_options = []

        if len(sys.argv) > 1:
            args = list(sys.argv[1:])
        else:
            args = []

        for arg in args:
            self.set_key_by_arg(arg)
            self.set_value_by_arg(arg)
            if self.processing_for_arg(arg):
                continue

            if self.key and self.value is not None:
                self.set_flag(self.key, self.value)
            else:
                print(f"Unrecognized arg '{arg}'! \nExiting the script.")
                sys.exit(1)

        if self.for_key and self.for_key_options:
            self.set_for_flag("options", self.for_key_options)

        if str(self.flag("start_dir")) == str(Path.cwd()):
            self.set_flag("start_dir", Path.cwd())
        if str(self.flag("save_dir")) == str(Path.cwd()):
            self.set_flag("save_dir", self.flag("start_dir"))

class FileDictionary:
    def __init__(self, flags):
        self.flags = flags

    EXTENSIONS = {
        'video': {'.mkv', '.m4v', '.mp4', '.avi', '.h264', '.hevc', '.ts', '.3gp', '.ogg',
                  '.flv', '.m2ts', '.mpeg', '.mpg', '.mov', '.ogm', '.webm', '.wmv'},

        'audio': {'.mka', '.m4a', '.aac', '.ac3', '.dts', '.dtshd', '.eac3', '.ec3', '.flac', '.mp2',
                  '.mpa', '.mp3', '.opus', '.truehd', '.wav', '.3gp', '.flv', '.m2ts', '.mkv', '.mp4',
                  '.avi', '.mpeg', '.mpg', '.mov', '.ts', '.ogg', '.ogm', '.webm', '.wma', '.wmv'},

        'subs': {'.ass', '.mks', '.ssa', '.sub', '.srt'},

        'font': {'.ttf', '.otf'},

        'mkvinfo_supported': {'.mkv', '.mka', '.mks', '.webm'},
    }
    EXTENSIONS['container'] = EXTENSIONS['video'] & EXTENSIONS['audio']

    KEYS = {
        'search_subsdir': ['надписи', 'sign', 'russiansub', 'russub', 'субтит', 'sub'],

        'skipdir': {'bonus', 'бонус', 'special', 'bdmenu', 'commentary', 'creditless', '__temp_files__',
                    'nc', 'nd', 'op', 'pv'},

        'skip_file': {"_replaced_", "_merged_", "_added_", "_temp_"},

        'lang': {'rus': {'надписи', 'субтитры', 'russian', 'rus'},
                 'eng': {'eng', 'english'}
                 }
    }
    KEYS['signs'] = {'надписи', 'signs'}

    @staticmethod
    def path_has_keyword(videopath, filepath, keywords):
        search_str = str(filepath.parent).replace(str(videopath.parent), '').lower()
        search_str = search_str + '/' + filepath.stem.replace(videopath.stem, '').lower()
        words = set(re.findall(r'\b\w+\b', search_str))
        if keywords & words:
            return True

    @staticmethod
    def clean_dirname(dir_name):
        if dir_name.startswith('[') and dir_name.endswith(']') and dir_name.count('[') == 1:
            cleaned_dir_name = dir_name.strip(' _.[]')
        else:
            cleaned_dir_name = dir_name.strip(' _.')
        return cleaned_dir_name

    @staticmethod
    def rm_repeat_sort_fonts(font_list):
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

    @classmethod
    def get_lang(cls, videopath, filepath):
        search_str = str(filepath.parent).replace(str(videopath.parent), "").lower()
        if not search_str:
            return
        words = set(re.findall(r'\b\w+\b', search_str))
        for lang, keywords in cls.KEYS['lang'].items():
            if words & keywords:
                return lang

    @classmethod
    def clean_tail(cls, tail):
        repeat = True
        while repeat:
            new_tail = re.sub(r'\.[a-zA-Z0-9]{1,3}\.', '', tail)
            if new_tail != tail:
                tail = new_tail
            else:
                repeat = False

        for ext in cls.EXTENSIONS['video'].union(cls.EXTENSIONS['audio'], cls.EXTENSIONS['subs']):
            if tail.lower().startswith(ext):
                tail = tail[len(ext):]
            if tail.lower().endswith(ext):
                tail = tail[:-len(ext)]

        tail = tail.strip(' _.')
        if tail.startswith('[') and tail.endswith(']') and tail.count('[') == 1:
            tail = tail.strip('[]')
        return tail

    @classmethod
    def get_trackname(cls, videopath, filepath):
        tail = filepath.stem[len(videopath.stem):]
        tail = cls.clean_tail(tail) if len(tail) > 2 else tail
        return tail if len(tail) > 2 else cls.clean_dirname(filepath.parent.name)

    @classmethod
    def find_subsdir_by_keys(cls, base_dir):
        search_method = base_dir.glob('*')
        found_dir_list = []
        repeat_search = True
        while repeat_search:
            repeat_search = False
            for subdir in sorted(search_method, reverse=True):
                cln_subdir_name = re.sub(r"[ .]", "", subdir.name).lower()
                for key in cls.KEYS['search_subsdir']:
                    if key in cln_subdir_name and subdir.is_dir():
                        found_dir_list.append(subdir)
                        search_method = subdir.rglob('*')
                        repeat_search = True
                        break
                if repeat_search:
                    break

        return found_dir_list

    @classmethod
    def find_ext_files(cls, search_dir, extensions, search_name="", recursive=False):
        if not search_dir.exists():
            return []
        search_method = search_dir.rglob('*') if recursive else search_dir.glob('*')
        found_files_list = []

        for filepath in sorted(search_method):
            if recursive and cls.path_has_keyword(search_dir, filepath.parent, cls.KEYS['skipdir']):
                continue

            filename = filepath.stem
            #если найденный файл содержит служебное имя пропускаем
            if any(key in filename for key in cls.KEYS['skip_file']):
                continue

            if (search_name in filename or filename in search_name) and filepath.is_file() and filepath.suffix.lower() in extensions:
                found_files_list.append(filepath)
        return found_files_list

    @classmethod
    def find_videodir_up(cls, flags, directory, extensions):
        filepath_list = cls.find_ext_files(directory, extensions)
        for filepath in filepath_list:
            count = 0
            search_dir = directory
            while count <= flags.flag("lim_search_up"):
                video_list = cls.find_ext_files(search_dir, cls.EXTENSIONS['video'], filepath.stem)
                for video in video_list:
                    #не выполняем если видео совпадает с файлом
                    if video == filepath:
                        continue
                    #проверяем что в видео есть видеодорожка, если нужно
                    if video.suffix not in cls.EXTENSIONS['container'] or video.parent != directory or FileInfo.file_has_video_track(video):
                        return video.parent

                search_dir = search_dir.parent
                count += 1
        return None

    @classmethod
    def find_dir_by_match_filenames(cls, video_list, search_dir, search_extensions, recursive):
        new_found_list = []
        for video in video_list:
            found_list = cls.find_ext_files(search_dir, search_extensions, video.stem, recursive)
            for found in found_list:
                #если найденный файл == видео пропускаем
                if found == video:
                    continue
                #проверяем что в видео есть видеодорожка, если нужно
                if video.suffix not in cls.EXTENSIONS['container'] or video.parent != search_dir or FileInfo.file_has_video_track(video):
                    return found.parent

    @classmethod
    def find_subsdir(cls, audio_dir, video_dir):
        recursive = False
        video_list = cls.find_ext_files(video_dir, cls.EXTENSIONS['video'])
        if video_dir == audio_dir:
            subs_dir = cls.find_dir_by_match_filenames(video_list, audio_dir, cls.EXTENSIONS['subs'], recursive)
            if subs_dir:
                return subs_dir
            else:
                return None

        search_dir_list = [audio_dir, video_dir]
        #поиск в стартовой директории и в видеодир без рекурсии
        for search_dir in search_dir_list:
            subs_dir = cls.find_dir_by_match_filenames(video_list, search_dir, cls.EXTENSIONS['subs'], recursive)
            if subs_dir:
                return subs_dir

        #поиск в сабдиректориях по запросу с рекурсией
        search_dir_list = [video_dir] + cls.find_subsdir_by_keys(video_dir)
        for search_dir in reversed(search_dir_list):
            for recursive in [False, True]:
                subs_dir = cls.find_dir_by_match_filenames(video_list, search_dir, cls.EXTENSIONS['subs'], recursive=recursive)
                if subs_dir:
                    return subs_dir
        return None

    @classmethod
    def find_fontdir(cls, subs_dir, video_dir):
        font_list = cls.find_ext_files(subs_dir, cls.EXTENSIONS['font'], "", recursive=True)
        if font_list:
            return font_list[0].parent
        else:
            if subs_dir != video_dir:
                font_list = cls.find_ext_files(subs_dir.parent, cls.EXTENSIONS['font'], "", recursive=True)
            if font_list:
                return font_list[0].parent
        return None

    @classmethod
    def files_from_found_dirs(cls, audio_dir, subs_dir, font_dir):
        audio_list = []
        subs_list = []
        font_list = []

        recursive=False
        if audio_dir:
            audio_list = cls.find_ext_files(audio_dir, cls.EXTENSIONS['audio'], "", recursive)
        if subs_dir:
            subs_list = cls.find_ext_files(subs_dir, cls.EXTENSIONS['subs'], "", recursive)
        if font_dir:
            font_list = cls.find_ext_files(font_dir, cls.EXTENSIONS['font'], "", recursive)
        return audio_list, subs_list, font_list

    @classmethod
    def files_from_start_dir(cls, search_dir):
        recursive = True
        audio_list = cls.find_ext_files(search_dir, cls.EXTENSIONS['audio'], "", recursive)
        subs_list = cls.find_ext_files(search_dir, cls.EXTENSIONS['subs'], "", recursive)
        font_list = cls.find_ext_files(search_dir, cls.EXTENSIONS['font'], "", recursive)
        return audio_list, subs_list, font_list

    def find_directories(self):
        self.video_dir = None
        self.audio_dir = None
        self.subs_dir = None
        self.font_dir = None
        search_dir = self.flags.flag("start_dir")

        # Поиск видеодиректории через аудио
        self.video_dir = __class__.find_videodir_up(self.flags, search_dir, __class__.EXTENSIONS['audio'])
        if self.video_dir:
            self.audio_dir = search_dir
            self.subs_dir = __class__.find_subsdir(self.audio_dir, self.video_dir)

        else: # Поиск видеодиректории через сабы
            self.video_dir = __class__.find_videodir_up(self.flags, search_dir, __class__.EXTENSIONS['subs'])
            if self.video_dir:
                self.subs_dir = search_dir

        if self.subs_dir: # Если найден сабдир, ищем фонтдир
            self.font_dir = __class__.find_fontdir(self.subs_dir, self.video_dir)

    def collect_files(self):
        if self.audio_dir or self.subs_dir:
            self.audio_list, self.subs_list, self.font_list = __class__.files_from_found_dirs(self.audio_dir, self.subs_dir, self.font_dir)

        else:
            self.audio_list, self.subs_list, self.font_list = __class__.files_from_start_dir(self.flags.flag("start_dir"))
            if self.font_list:
                self.font_list = __class__.rm_repeat_sort_fonts(self.font_list)

    def create_file_dicts(self):
        new_video_list = []
        self.audio_dict = {}
        self.subs_dict = {}

        for video in self.video_list:
            skip = False
            save = False
            video_track = False
            self.audio_dict[str(video)] = []
            self.subs_dict[str(video)] = []

            for audio in self.audio_list:
                #если audio совпадает с video пропускаем audio или video
                if video == audio:
                    if video_track or FileInfo.file_has_video_track(video):
                        video_track = True
                        continue
                    else:
                        skip = True
                        break

                if video.stem in audio.stem:
                    self.audio_dict[str(video)].append(audio)
                    save = True

            if skip:
                continue

            for subs in self.subs_list:
                if video.stem in subs.stem:
                    self.subs_dict[str(video)].append(subs)
                    save = True

            if save:
                new_video_list.append(video)

        self.video_list = new_video_list

    def find_all_files(self):
        self.find_directories()

        search_dir = self.video_dir if self.video_dir else self.flags.flag("start_dir")
        self.video_list = __class__.find_ext_files(search_dir, __class__.EXTENSIONS['video'])
        if not self.video_list:
            self.video_list = []
            return

        self.collect_files()
        self.create_file_dicts()

        if not self.video_list: #пробуем найти mkv для обработки линковки
            self.audio_dict = self.subs_dict = self.font_list = {}
            self.video_list = __class__.find_ext_files(self.flags.flag("start_dir"), ".mkv")

class Merge(FileDictionary):
    def set_output_path(self, tail=""):
        if self.out_pname or self.out_pname_tail:
            name = f"{self.out_pname}{self.current_index+1:0{len(str(self.video_list_len))}d}{self.out_pname_tail}"
            self.output = Path(self.flags.flag("save_dir")) / f"{name}.mkv"

        else:
            k = [self.video, "video"]
            partname = f"{self.video.stem}{tail}"
            if self.audio_list:
                if self.merge_truefalse_flag(*k, "orig_audio"):
                    partname = partname + "_added_audio"
                else:
                    partname = partname + "_replaced_audio"

            if self.subs_list:
                if self.merge_truefalse_flag(*k, "orig_subs"):
                    partname = partname + "_added_subs"
                else:
                    partname = partname + "_replaced_subs"

            if self.font_list:
                if self.merge_truefalse_flag(*k, "orig_fonts"):
                    partname = partname + "_added_fonts"
                else:
                    partname = partname + "_replaced_fonts"

            self.output = Path(self.flags.flag("save_dir")) / f"{partname}.mkv"

    def for_merge_flag(self, filepath, filegroup, key3):
        flag = None
        flag_list = []
        keys2 = [str(filepath), filegroup, str(filepath.parent)]

        if self.mkv_linking and self.matching_keys:
            count = 0
            for key2 in keys2:
                if key2 in self.matching_keys:
                    keys2[count] = self.matching_keys[key2]
                count += 1


        if self.for_priority == "file_first":
            for key2 in keys2:
                flag = self.flags.for_flag(key2, key3)
                if flag is not None:
                    break

        else:
            for key2 in reversed(keys2):
                if self.for_priority == "dir_first":
                    flag = self.flags.for_flag(key2, key3)
                    if flag is not None:
                        break

                else:
                    flag_list.append(self.flags.for_flag(key2, key3))

                if len(flag_list) > 0:

                    if key3 == "options":
                        temp = []
                        for flg in flag_list:
                            if flg:
                                temp.append(flg)

                        if temp:
                            flag = temp

                    elif key3 in Flags.TYPES['truefalse']:
                        flag = not False in flag_list

                    elif key3 in Flags.TYPES['str']:
                        flag = ""
                        for flg in flag_list:
                            if flg:
                                flag += flg

        if flag is None and key3 == "options":
            return []
        return flag

    def merge_flag(self, filepath, filegroup, key):
        k = [filepath, filegroup]
        flag = self.for_merge_flag(*k, key)
        if flag is None and filegroup == "video" and "orig_" in key:
            flag = self.for_merge_flag(*k, key.replace("orig_", ""))
        if flag is None and key != "options":
            flag = self.flags.flag(key, default_if_missing=False)
        return flag

    def merge_truefalse_flag(self, filepath, filegroup, key):
        flg1 = self.merge_flag(filepath, filegroup, key)
        default_if_missing = not self.strict_true and not self.strict_false
        flg2 = self.flags.flag(key, default_if_missing)

        if self.strict_true:
            return True if flg1 is True or (flg1 is None and flg2 is True) else False
        elif self.strict_false:
            return False if flg1 is False or (flg1 is None and flg2 is False) else True
        else:
            return False if flg1 is False or (flg1 is None and not flg2) else True

    def switch_stricts(self, strict):
        if self.pro:
            self.strict_true = strict
            self.strict_false = not strict

    def get_enableds_pcommand(self, filepath, filegroup):
        part = []
        self.switch_stricts(False)
        for group in ['video', 'audio', 'subs']:
            k = [filepath, group]
            val = '' if self.merge_truefalse_flag(*k, 'enabled') else ':0'
            for tid in FileInfo.get_track_type_tids(*k):
                part.extend(["--track-enabled-flag", f"{tid}{val}"])
        self.switch_stricts(True)
        return part

    def get_common_part_command(self, filepath, filegroup):
        part = []
        k = [filepath, filegroup]

        group = filegroup
        if filegroup == 'subs' and super().path_has_keyword(self.video, filepath, super().KEYS['signs']):
            group = 'signs'
        self.cmd.setdefault(group, {})[f'{self.fid}'] = filepath

        if not self.merge_truefalse_flag(*k, "video"):
            part.append("--no-video")
        if not self.merge_truefalse_flag(*k, "global_tags"):
            part.append("--no-global-tags")
        if not self.merge_truefalse_flag(*k, "chapters"):
            part.append("--no-chapters")

        self.switch_stricts(True)
        if self.merge_truefalse_flag(*k, "enableds"):
            part.extend(self.get_enableds_pcommand(*k))
        self.switch_stricts(False)
        part.extend(self.for_merge_flag(*k, "options"))
        return part

    def get_part_command_for_video(self):
        part = []
        k = [self.merge_video_list[0], "video"]

        if not self.merge_truefalse_flag(*k, "orig_audio"):
            part.append("--no-audio")
        if self.subs_dir and self.subs_list or not self.merge_truefalse_flag(*k, "orig_subs"):
            part.append("--no-subtitles")
        if self.orig_font_list or not self.merge_truefalse_flag(*k, "orig_fonts"):
            part.append("--no-attachments")
        part.extend(self.get_common_part_command(*k))
        return part

    def get_trackname_pcommand(self, filepath, filegroup):
        part = []
        k = [filepath, filegroup]

        forced = self.merge_flag(*k, "trackname")
        if not forced and FileInfo.get_file_info(filepath, "Name:"):
            return []

        trackname = forced if forced else super().get_trackname(self.video, filepath)
        if not trackname:
            return []

        track_id_list = FileInfo.get_track_type_tids(filepath, filegroup)
        for track_id in track_id_list:
            part.extend(["--track-name", f"{track_id}:{trackname}"])
        return part

    def get_lang_pcommand(self, filepath, filegroup):
        part = []
        k = [filepath, filegroup]

        forced = self.merge_flag(*k, "lang")
        if not forced and FileInfo.get_file_info(filepath, "Language:"):
            return []

        lang = forced if forced else super().get_lang(self.video, filepath)
        if not lang:
            return []

        track_id_list = FileInfo.get_track_type_tids(filepath, filegroup)
        for track_id in track_id_list:
            part.extend(["--language", f"{track_id}:{lang}"])
        return part

    def get_part_command_for_file(self, filepath, filegroup):
        part = []
        k = [filepath, filegroup]

        if not self.merge_truefalse_flag(*k, "audio"):
            part.append("--no-audio")
        if not self.merge_truefalse_flag(*k, "subs"):
            part.append("--no-subtitles")
        if not self.merge_truefalse_flag(*k, "fonts"):
            part.append("--no-attachments")

        if not self.mkv_linking or self.mkv_linking and not filepath.parent.name.startswith("orig_"):
            self.switch_stricts(True)
            if self.merge_truefalse_flag(*k, "tracknames"):
                part.extend(self.get_trackname_pcommand(*k))
            if self.merge_truefalse_flag(*k, "langs"):
                part.extend(self.get_lang_pcommand(*k))
            self.switch_stricts(False)

        part.extend(self.get_common_part_command(*k))
        return part

    def set_delay_if_need(self, filepath):
        paths = [self.video, filepath]
        if super().path_has_keyword(*paths, {'orig_audio', 'orig_subs'}):
            self.delayeds.setdefault('orig', []).append(filepath)
            return True

        unlocales = set()
        for lang, keys in super().KEYS['lang'].items():
            if lang != self.flags.flag('locale'):
                unlocales.update(keys)

        if super().path_has_keyword(*paths, unlocales):
            self.delayeds.setdefault('nonlocale', []).append(filepath)
            return True

    def set_def_force_pcommand(self):
        lim = self.flags.flag('lim_default_ttype')
        lim_f = self.flags.flag('lim_forced_signs')

        for group in ['signs', 'subs', 'audio', 'video']:
            for fid, filepath in self.cmd.get(group, {}).items():
                s_group = group if group != 'signs' else 'subs'
                k = [filepath, s_group]

                self.switch_stricts(True)
                add_defaults = self.merge_truefalse_flag(*k, 'defaults')
                add_forceds = self.merge_truefalse_flag(*k, 'forceds')
                if add_defaults or add_forceds:

                    for group2 in ['subs', 'audio', 'video']:
                        k = [filepath, group2]

                        for tid in FileInfo.get_track_type_tids(*k):
                            part = []

                            if add_defaults:
                                self.switch_stricts(False)
                                var = self.merge_truefalse_flag(*k, 'default')
                                cnt = self.cmd.setdefault('cnt', {}).setdefault('default', {}).setdefault(f'{group2}', 0)

                                if var and self.pro:
                                    value = ''
                                elif var and cnt < lim and (group2 != 'subs' or (group2 == 'subs' and (group == 'signs' or not self.cmd.get('audio', {})))):
                                    value = ''
                                else:
                                    value = ':0'

                                part.extend(['--default-track-flag', f'{tid}{value}'])
                                if not value:
                                    self.cmd['cnt']['default'][group2] += 1

                            if add_forceds:
                                self.switch_stricts(True)
                                var = self.merge_truefalse_flag(*k, 'forced')
                                cnt = self.cmd.setdefault('cnt', {}).setdefault('forced', {}).setdefault(f'{group2}', 0)
                                forced_signs = self.merge_truefalse_flag(*k, 'forced_signs')

                                value2 = '' if var or group == 'signs' and group2 == 'subs' and forced_signs and cnt < lim_f else ':0'

                                part.extend(['--forced-display-flag', f'{tid}{value2}'])
                                if not value2:
                                    self.cmd['cnt']['forced'][group2] += 1

                            self.cmd['cmd'][f'{fid}'][:0] = part

    def get_track_orders(self):
        self.switch_stricts(True)
        if not self.merge_truefalse_flag(self.merge_video_list[0], 'video', 't_orders'):
            return []

        orders = ''
        for group in ['video', 'audio', 'signs', 'subs']:
            for fid, filepath in self.cmd.get(group, {}).items():
                s_group = group if group != 'signs' else 'subs'
                for tid in FileInfo.get_track_type_tids(filepath, s_group):
                    orders = orders + f'{fid}:{tid},'

            if group in {'audio', 'subs'}:
                for fid, filepath in self.cmd.get('video', {}).items():
                    for tid in FileInfo.get_track_type_tids(filepath, group):
                        orders = orders + f'{fid}:{tid},'

        return ['--track-order', orders[:-1]] if orders else []

    def get_merge_command(self):
        command = [str(Tools.mkvmerge), "-o", str(self.output)]
        self.cmd = {}

        self.fid = 0
        cmd = self.cmd.setdefault('cmd', {}).setdefault(f'{self.fid}', [])
        self.switch_stricts(False)
        part = self.get_part_command_for_video()
        cmd.extend(part + [str(self.merge_video_list[0])])
        for video in self.merge_video_list[1:]:
            cmd.extend([f"+{str(video)}"])

        self.delayeds = {}
        for audio in self.audio_list:
            if self.set_delay_if_need(audio):
                continue
            self.fid += 1
            cmd = self.cmd.setdefault('cmd', {}).setdefault(f'{self.fid}', [])
            cmd.extend(self.get_part_command_for_file(audio, "audio") + [str(audio)])
        for key in reversed(list(self.delayeds.keys())):
            for audio in self.delayeds[key]:
                self.fid += 1
                cmd = self.cmd.setdefault('cmd', {}).setdefault(f'{self.fid}', [])
                cmd.extend(self.get_part_command_for_file(audio, "audio") + [str(audio)])

        self.delayeds = {}
        for subs in self.subs_list:
            if self.set_delay_if_need(subs):
                continue
            self.fid += 1
            cmd = self.cmd.setdefault('cmd', {}).setdefault(f'{self.fid}', [])

            tid = self.cp1251_for_subs.get(str(subs), None)
            if tid:
                cmd.extend(["--sub-charset", f"{tid}:windows-1251"])
            cmd.extend(self.get_part_command_for_file(subs, "subs") + [str(subs)])
        for key in reversed(list(self.delayeds.keys())):
            for subs in self.delayeds[key]:
                self.fid += 1
                cmd = self.cmd.setdefault('cmd', {}).setdefault(f'{self.fid}', [])
                cmd.extend(self.get_part_command_for_file(subs, "subs") + [str(subs)])

        self.set_def_force_pcommand()

        command.extend(self.get_track_orders())
        for fid, cmd in self.cmd['cmd'].items():
            command.extend(cmd)

        for font in self.merge_font_list:
            command.extend(self.for_merge_flag(font, "fonts", "options") + ["--attach-file", str(font)])

        return command

    def processing_error_warning_merge(self, command_out, lmsg):
        cleaned_out = ''.join(command_out.split()).lower()
        last_line_out = command_out.splitlines()[-1]
        cleaned_lline_out = ''.join(last_line_out.split()).lower()

        if not self.cp1251_for_subs and "textsubtitletrackcontainsinvalid8-bitcharacters" in cleaned_out:
            print("Invalid 8-bit characters in subs file!")
            for line in command_out.splitlines():
                if line.startswith("Warning") and "invalid 8-bit characters" in line:
                    filename_match = re.search(r"'(/[^']+)'", line)
                    filename = filename_match.group(1) if filename_match else None
                    filepath = TypeConverter.str_to_path(filename)

                    track_id_match = re.search(r"track (\d+)", line)
                    track_id = track_id_match.group(1) if track_id_match else None
                    if filename and track_id:
                        self.cp1251_for_subs[str(filepath)] = track_id

            if self.cp1251_for_subs:
                print("Trying to generate with windows-1251 coding.")
                self.execute_merge()
                self.cp1251_for_subs = {}
                return

        if not cleaned_lline_out.startswith("error"):
            print(lmsg)

            if "thecodec'sprivatedatadoesnotmatch" in cleaned_out:
                print(f"Attention! The video file maybe corrupted because video parts have mismatched codec parameters. Please check the video file.")

        else:
            if "containschapterswhoseformatwasnotrecognized" in cleaned_lline_out:
                print(f"{last_line_out}\nTrying to generate without chapters.")
                self.flags.set_flag("chapters", False)
                self.execute_merge()
                self.flags.set_flag("chapters", True)

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

    def extract_orig_fonts(self):
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

        self.orig_font_list = super().find_ext_files(self.orig_font_dir, super().EXTENSIONS["font"])

    def set_common_merge_vars(self):
        self.mkv_linking = False
        self.video_list_len = len(self.video_list)
        self.out_pname = self.flags.flag("out_pname")
        self.out_pname_tail = self.flags.flag("out_pname_tail")
        self.linked_uid_info_dict = {}
        self.matching_keys = {}
        self.temp_dir = Path(self.flags.flag("save_dir")) / f'__temp_files__.{str(uuid.uuid4())[:8]}'
        self.orig_font_dir = Path(self.temp_dir) / "orig_fonts"
        self.for_priority = self.flags.flag("for_priority")
        self.lim_gen = self.flags.flag("lim_gen")
        self.add_tracknames = self.flags.flag("add_tracknames")
        self.count_gen = 0
        self.count_gen_before = 0

        self.start_range = self.flags.flag("range_gen")[0]
        self.end_range = self.flags.flag("range_gen")[1]
        if self.start_range > 0:
            self.start_range = self.start_range - 1
            self.end_range = self.end_range - 1
        self.current_index = self.start_range

    def get_merge_file_list(self, filegroup, filelist):
        filepath_list = []
        if self.flags.flag(filegroup):
            for filepath in filelist:
                if self.for_merge_flag(filepath, filegroup, "files") is not False:
                    filepath_list.append(filepath)
        return filepath_list

    def set_files_merge_vars(self, k):
        self.mkv_linking = False
        self.strict_true = False
        self.strict_false = False
        self.cmd = {}
        self.pro = self.merge_flag(*k, "pro")
        self.orig_font_list = []
        self.cp1251_for_subs = {}

        self.audio_list = self.get_merge_file_list("audio", self.audio_dict.get(str(self.video), []))
        self.subs_list = self.get_merge_file_list("subs", self.subs_dict.get(str(self.video), []))
        self.merge_font_list = self.get_merge_file_list("fonts", self.font_list)

    def sort_orig_fonts(self, k):
        if self.pro and self.merge_flag(*k, "sort_orig_fonts") is not True:
            return

        if self.merge_truefalse_flag(*k, "sort_orig_fonts") and self.merge_truefalse_flag(*k, "orig_fonts"):
            self.extract_orig_fonts()
            if self.orig_font_list and self.merge_font_list:
                self.merge_font_list = super().rm_repeat_sort_fonts(self.merge_font_list + self.orig_font_list)
            elif self.orig_font_list:
                self.merge_font_list = self.orig_font_list

    def delete_temp_files(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def merge_all_files(self):
        self.set_common_merge_vars()

        for self.video in self.video_list[self.start_range:]:
            k = [self.video, "video"]
            if self.count_gen >= self.lim_gen or self.current_index > self.end_range:
                break
            if self.for_merge_flag(*k, "files") is False:
                self.current_index += 1
                continue

            self.merge_video_list = [self.video]
            self.set_files_merge_vars(k)

            self.set_output_path()
            if self.video.suffix == ".mkv":
                linked = LinkedMKV(self)

                if linked.mkv_has_segment_linking():
                    self.mkv_linking = True
                    self.set_output_path("_merged_video")

                else:
                    if not self.audio_list and not self.subs_list and not self.font_list:
                        self.current_index += 1
                        continue #пропускаем если нет ни линковки ни аудио ни сабов ни шрифтов

            if self.output.exists():
                self.count_gen_before += 1
                self.current_index += 1
                continue

            if self.mkv_linking:
                linked.processing_linked_mkv()
                self.matching_keys.update(linked.matching_keys)

            self.sort_orig_fonts(k)
            self.execute_merge()
            self.count_gen += 1
            self.current_index += 1

        self.delete_temp_files()

class LinkedMKV:
    def __init__(self, merge_instance):
        self.merge = merge_instance

    @staticmethod
    def find_video_with_uid(search_dir, target_uid):
        video_list = FileDictionary.find_ext_files(search_dir, ".mkv", recursive=True)
        for video in reversed(video_list):
            if FileInfo.get_file_info(video, "Segment UID:").lower() == target_uid.lower():
                return video

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
                defacto_end = defacto_start + FileInfo.get_file_info(segment, "Duration:")
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
            defacto_end = FileInfo.get_file_info(segment, "Duration:")
            offset_start = timedelta(0)
            offset_end = timedelta(0)

        return segment, defacto_start, defacto_end, offset_start, offset_end

    @staticmethod
    def extract_track(input_file, output, track_id):
        command = [str(Tools.mkvextract), "tracks", str(input_file), f"{track_id}:{str(output)}"]
        CommandExecutor.execute(command)

    @staticmethod
    def split_file(input_file, partname, start, end, file_type="video", orig_fonts=True, track_id=""):
        command = [str(Tools.mkvmerge), "-o", str(partname), "--split", f"timecodes:{start},{end}", "--no-global-tags", "--no-chapters", "--no-subs"]
        if "video" in file_type:
            command.append("--no-audio")
            if not orig_fonts:
                command.append("--no-attachments")
        else:
            command.extend(["--no-video", "--no-attachments"])
            if track_id:
                command.extend(["-a", f"{track_id}"])
        command.append(str(input_file))

        # Выполняем команду и ищем переназначения
        mkvmerge_stdout = CommandExecutor.get_stdout(command)
        segment, defacto_start, defacto_end, offset_start, offset_end = __class__.get_segment_info(mkvmerge_stdout, partname, start, end)
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

    def not_found_uid_video(self, uid):
        print(f"Error!\nVideo file with uid {uid} not found in the video directory '{str(self.merge.video.parent)}'\nThis file is part of the linked video '{str(self.merge.video)}' and is required for merging. Please move this file to the video directory and re-run the script.")
        self.merge.delete_temp_files()
        sys.exit(1)

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
                            temp_video = __class__.find_video_with_uid(self.merge.video.parent, uid)
                            if not temp_video:
                                self.not_found_uid_video(uid)

                        else:
                            temp_video = self.merge.video
                        temp_end = FileInfo.get_file_info(temp_video, "Duration:")

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
            self.to_split = __class__.find_video_with_uid(self.video_dir, self.uid)

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
            if not self.to_split:
                self.not_found_uid_video(self.uid)

            self.prev_lengths = self.lengths
            self.segment, length, self.offset_start, self.offset_end = __class__.split_file(self.to_split, self.partname, self.start, self.end, orig_fonts=self.merge.merge_truefalse_flag(self.merge.video, "video", "orig_fonts"))
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
            a_segment, a_length, offset_start, offset_end = __class__.split_file(source, partname, start, end, file_type="audio", track_id=self.track_id)
            if offset_start > timedelta(milliseconds=200) or offset_end > timedelta(milliseconds=200):
                new_start = start - offset_start if start - offset_start > timedelta(0) else start
                new_end = end - offset_end
                a_segment, a_length, offset_start, offset_end = __class__.split_file(source, partname, new_start, new_end, file_type="audio", track_id=self.track_id)

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
            a_segment, a_length, split_offset_start, split_offset_end = __class__.split_file(self.audio, partname, start, end, file_type="audio")

            if split_offset_start > timedelta(milliseconds=200) or split_offset_end > timedelta(milliseconds=200):
                new_start = start - split_offset_start if start - split_offset_start > timedelta(0) else start
                new_end = end - split_offset_end
                a_segment, a_length, *_ = __class__.split_file(self.audio, partname, new_start, new_end, file_type="audio")

            if add_compensation:
                compensation_length = length - a_length
                if compensation_length > timedelta(milliseconds=500):
                    partname = Path(self.retimed_audio.parent) / f"compensation_{count}.mka"
                    compensation_end = compensation_start + compensation_length
                    compensation_segment, compensation_length, *_ = __class__.split_file(self.audio, partname, compensation_start, compensation_end, file_type="audio")
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
        if self.merge.merge_truefalse_flag(self.merge.video, "video", "orig_audio"):
            audio_track_id_list = FileInfo.get_track_type_tids(self.merge.video, "audio")
            for self.track_id in audio_track_id_list:
                self.get_retimed_segments_orig_audio()
                orig_audio = Path(self.temp_orig_audio_dir) / f"{count}.mka"
                __class__.merge_file_segments(self.a_segment_list, orig_audio)

                self.retimed_audio_list.append(orig_audio)
                count += 1

        for self.audio in self.merge.audio_list:
            self.retimed_audio = Path(self.temp_ext_audio_dir) / self.audio.parent.name / f"{self.audio.stem}.{count:03}..mka"
            self.get_retimed_segments_ext_audio()
            __class__.merge_file_segments(self.a_segment_list, self.retimed_audio)

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

        if self.merge.merge_truefalse_flag(self.merge.video, "video", "orig_subs"):
            self.segment_orig_sub_list = []

            #проверяем сколько дорожек субтитров в исходном видео
            sub_track_id_list = FileInfo.get_track_type_tids(self.merge.video, "subs")
            for self.track_id in sub_track_id_list:
                count_temp = 0
                for source in self.source_list:
                    split_original_sub = Path(self.temp_orig_subs_dir) / f"{count + count_temp}.ass"
                    __class__.extract_track(source, split_original_sub, self.track_id)
                    self.segment_orig_sub_list.append(split_original_sub)
                    count_temp += 1

                self.retime_original_sub()
                self.retimed_sub_list.append(self.retimed_original_sub)
                count += 1

        for subs in self.merge.subs_list:
            self.sub_for_retime = Path(self.temp_ext_subs_dir) / subs.parent.name / f"{subs.stem}.{count:03}..ass"
            if subs.suffix != ".ass":
                print(f"\nSkip subtitles! {str(subs)} \nThese subtitles need to be retimed because the video file has segment linking. Retime is only possible for .ass subs.")
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

        count = 0
        for old_key2 in old_keys2:
            for_dict = self.merge.flags.flag("for")
            if old_key2 in for_dict:
                self.matching_keys[new_keys2[count]] = old_key2
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
        self.merge.subs_list = self.retimed_sub_list

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
    if flags.flag("lim_gen") == 0:
        print("A new video can't be generated because the limit-generate set to 0. \nExiting the script.")
        sys.exit(0)

    Tools.set_mkvtools_paths()

    print(f"\nTrying to generate a new video in the save directory '{str(flags.flag("save_dir"))}' using files from the start directory '{str(flags.flag("start_dir"))}'.")

    merge = Merge(flags)
    merge.find_all_files()
    lmsg = f"Files for generating a new video not found. Checked the directory '{str(flags.flag("start_dir"))}', its subdirectories and {flags.flag("lim_search_up")} directories up."

    if not merge.video_list:
        print(lmsg)
        sys.exit(0)
    elif flags.flag("range_gen")[0] > len(merge.video_list):
        print(f"A new video can't be generated because the start range-generate exceeds the number of video files. \nExiting the script.")
        sys.exit(0)

    merge.merge_all_files()

    if merge.count_gen_before:
        print(f"\n{merge.count_gen_before} video files in the save directory '{str(flags.flag("save_dir"))}' had generated names before the current run of the script. Generation for these files has been skipped.")

    if merge.count_gen:
        print(f"\nThe script was executed successfully. {merge.count_gen} video files were generated in the directory '{str(flags.flag("save_dir"))}'")
    else:
        print(lmsg)

if __name__ == "__main__":
    main()
