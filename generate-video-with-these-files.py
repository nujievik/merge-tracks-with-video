"""
generate-video-with-these-files-v0.8.1

Licensed under GPL-3.0.
This script requires third-party tools: Python, MKVToolNix and FFprobe (part of FFmpeg).
These tools are licensed under Python PSF, GPL-2.0, and LGPL-2.1, respectively.
See LICENSE file for details.
"""
import sys
import os
import shutil
import re
import subprocess
import shlex
import uuid
import locale
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from datetime import timedelta

class CommandExecutor:
    @staticmethod
    def execute(command, exit_after_error=True, rm=None):
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE)
 
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if not exit_after_error:
                return False
            print(f"Error executing the command:\n{command}\n{e.output.decode()}\nExiting the script.")
            if rm: rm()
            sys.exit(1)

    @staticmethod
    def get_stdout(command, exit_after_error=True, rm=None):
        try:
            return subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout.decode()

        except subprocess.CalledProcessError as e:
            if not exit_after_error:
                return e.output.decode(), 1
            print(f"Error executing the command:\n{command}\n{e.output.decode()}\nExiting the script.")
            if rm: rm()
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
    def timedelta_to_str(td, hours_place=1, decimal_place=2):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        d, dp = td.microseconds, decimal_place
        decimal = int(d / (10 ** (6 - dp))) if dp <= 6 else d * 10 ** (dp - 6)
        return f'{hours:0{hours_place}}:{minutes:02}:{seconds:02}.{decimal:0{decimal_place}}'

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
    def cut_stdout_for_track(stdout_lines, tid):
        cutted = []

        save = False
        pattern1 = rf"\s*Track number:\s*{tid}"
        pattern2 = rf"\s*Track number:\s*{tid+1}"
        for line in stdout_lines:
            if re.search(pattern1, line):
                save = True
            if re.search(pattern2, line):
                break

            if save:
                cutted.append(line)
        return cutted

    @classmethod
    def get_file_info(cls, filepath, query, tid=None):
        if filepath.suffix not in FileDictionary.EXTENSIONS['mkvtools_supported']:
            return
        tid = tid + 1 if tid is not None else None

        stdout_lines = CommandExecutor.get_stdout([str(Tools.mkvinfo), str(filepath)]).splitlines()
        if tid:
            stdout_lines = cls.cut_stdout_for_track(stdout_lines, tid)

        for line in stdout_lines:
            if query in line:
                if "Segment UID:" in query:
                    uid_hex = line.strip()
                    uid_clean = "".join(byte[2:] for byte in uid_hex.split() if byte.startswith("0x"))
                    return uid_clean

                match = re.search(rf".*{query}\s*(.*)", line)

                if "Duration:" in query:
                    if match:
                        file_duration = match.group(1).strip()
                        file_duration_timedelta = TypeConverter.str_to_timedelta(file_duration)
                        return file_duration_timedelta

                if match:
                    value = match.group(1).strip()
                    return value if value != 'und' else None

class Tools():
    mkvextract = mkvinfo = mkvmerge = None
    ffprobe = None

    @staticmethod
    def available_tool(tool):
        command = [str(tool), '-v', 'quiet', '-h'] if tool.stem == 'ffprobe' else [str(tool), '-h']
        return False if CommandExecutor.execute(command, exit_after_error=False) is False else True

    @classmethod
    def find_tool(cls, tool):
        tail = '.exe' if os.name == 'nt' else ''
        potential_paths = [Path.cwd() / f'{tool}{tail}', Path(tool)]

        if getattr(sys, 'frozen', False):
            bundled = Path(sys._MEIPASS) / f'tools/{tool}{tail}'
            if bundled.exists():
                potential_paths.insert(0, bundled)

        if os.name == 'nt' and tool != 'ffprobe':  # Windows
            potential_paths.extend([
                Path(os.environ.get("PROGRAMFILES", "")) / "MkvToolNix" / f"{tool}.exe",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "MkvToolNix" / f"{tool}.exe",
                Path.home() / 'Downloads' / 'mkvtoolnix' / f"{tool}.exe"
            ])

        for path in potential_paths:
            if cls.available_tool(path):
                return path

    @classmethod
    def set_tools_paths(cls):
        tools = ['mkvextract', 'mkvinfo', 'mkvmerge', 'ffprobe']

        for tool in tools:
            setattr(cls, tool, cls.find_tool(tool))

        if None in [cls.mkvextract, cls.mkvinfo, cls.mkvmerge]:
            print("Error! MKVToolNix is not installed. Please install MKVToolNix "
                "and re-run the script:\nhttps://mkvtoolnix.download/downloads.html")
            sys.exit(1)

    @classmethod
    def ffprobe_installed(cls, exit_if_none=True):
        if not cls.ffprobe:
            print('Error! FFprobe (part of FFmpeg) is not installed. This tool is required for splitted MKV. '
                'Please install this tool, add to the OS Path and re-run the script:\nhttps://ffmpeg.org/download.html')
            if exit_if_none:
                sys.exit(1)
            return False
        return True

class Flags():
    def __init__(self):
        self.__flags = {}
        self.set_locale()

    DEFAULT = {
        "start_dir": Path.cwd(),
        "save_dir": Path.cwd(),
        'locale': 'rus',
        'out_pname': '', 'out_pname_tail': '',
        'tname': '',
        'tlang': '',
        "lim_search_up": 3,
        "lim_gen": 99999,
        'lim_forced_ttype': 0,
        'lim_default_ttype': 1,
        'lim_enabled_ttype': 99999,
        'lim_forced_signs': 1,
        "range_gen": [0, 99999],
        'rm_chapters': set(),
        "pro": False,
        "extended_log": False,
        "global_tags": True,
        "chapters": True,
        'files': True,
        "video": True,
        "audio": True,
        "orig_audio": True,
        "subs": True,
        "orig_subs": True,
        "fonts": True,
        "orig_fonts": True,
        "sort_orig_fonts": True,
        "tnames": True,
        'tlangs': True,
        'enableds': True, 'enabled': True,
        'defaults': True, 'default': True,
        'forceds': True, 'forced': False, 'forced_signs': False,
        't_orders': True,
        'linking': True, 'opening': True, 'ending': True,
        'force_retiming': True,
        'for_priority': 'file_first', #dir_first, mix
        'for': {}
    }

    TYPES = {}
    for flag, value in DEFAULT.items():
        if isinstance(value, Path):
            key = 'path'
        elif isinstance(value, bool):
            key = 'bool'
        elif isinstance(value, str):
            key = 'str'
        elif isinstance(value, int):
            key = 'num'
        elif isinstance(value, list):
            key = 'range'
        elif isinstance(value, set):
            key = 'set'
        else:
            key = ''
        TYPES.setdefault(key, set()).add(flag)

    STRICT_BOOL = {True: {'pro', 'extended_log', 'tlangs', 'tnames', 'enableds', 'sort_orig_fonts',
                          'defaults', 'forceds', 'forced_signs', 't_orders'}}
    STRICT_BOOL[False] = TYPES['bool'] - STRICT_BOOL[True]

    FOR_SEPARATE_FLAGS = TYPES['bool'].union({'tname', 'tlang'})

    MATCHINGS = {'part': {'pro_mode': 'pro',
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
                          'track_orders': 't_orders',
                          'track_type': 'ttype',
                          'trackname': 'tname',
                          'language': 'lang',
                          'track_lang': 'tlang'
                    },

                'full': {'lang': 'tlang', 'langs': 'tlangs',
                         'name': 'tname', 'names': 'tnames',
                         'op': 'opening', 'ed': 'ending'}
            }

    def set_flag(self, key, value, check_exists=False):
        if not check_exists or key in self.__flags:
            self.__flags[key] = value
        else:
            print(f"Error flag '{key}' not found, flag not set.")

    def flag(self, key, default_if_missing=True):
        value = self.__flags.get(key, None)
        if value is None and default_if_missing:
            value = self.__class__.DEFAULT.get(key, None)
        return value

    def set_for_flag(self, key3, value, key2=None):
        key2 = key2 if key2 else self.for_key
        if key3 == 'options':
            value = self.__flags.get('for', {}).get(key2, {}).get('options', []) + value
        self.__flags.setdefault('for', {}).setdefault(key2, {})[key3] = value

    def for_flag(self, key2, key3):
        return self.__flags.get('for', {}).get(key2, {}).get(key3, None)

    def set_key_by_arg(self, arg):
        self.key = None

        if not arg.startswith(("-", "+")) and not self.for_key:
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
            for find, replace in self.__class__.MATCHINGS['part'].items():
                if find in self.key:
                    self.key = self.key.replace(find, replace)
                    repeat = True
        for find, replace in self.__class__.MATCHINGS['full'].items():
            if find == self.key:
                self.key = replace
                break

    def get_bool_by_arg(self, arg):
        if self.key in self.__class__.TYPES['bool']:
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

            elif {self.key, f'save_{self.key}'} & self.__class__.TYPES['path']:
                self.value = TypeConverter.str_to_path(value.strip("'\""))
                if f'save_{self.key}' in self.__class__.TYPES['path']:
                    self.key = f'save_{self.key}'

            elif self.key in self.__class__.TYPES['str']:
                self.value = value.strip("'\"")

            elif self.key in self.__class__.TYPES['set']:
                self.value = set(value.strip("'\"").split(','))

            elif number is not None and self.key in self.__class__.TYPES['num']:
                self.value = number

            elif number is not None and self.key in self.__class__.TYPES['range']:
                num2 = self.flag(self.key)[1]
                self.value = [number, num2]

            elif self.key in self.__class__.TYPES['range']:
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
                        num2 = self.flag(self.key)[1]
                    elif num2 is not None:
                        num1 = self.flag(self.key)[0]

                    if num1 is not None:
                        self.value = [num1, num2]

        return self.value

    def set_value_by_arg(self, arg):
        self.value = None
        if not arg.startswith(("-", "+")) and not self.for_key:
            self.value = TypeConverter.str_to_path(arg.strip("'\""))
        elif self.get_bool_by_arg(arg):
            pass
        elif self.get_valueflag_by_arg(arg):
            pass

    def processing_for_arg(self, arg):
        if self.key == 'for':
            return True

        elif self.for_key:
            if self.key in self.__class__.FOR_SEPARATE_FLAGS and self.value is not None:
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

        if str(self.flag("save_dir")) == str(Path.cwd()):
            self.set_flag("save_dir", self.flag("start_dir"))

    def set_locale(self):
        for element in locale.getlocale():
            locale_words = set(element.split('_'))
            for lang, keys in FileDictionary.KEYS['lang'].items():
                if keys & locale_words:
                    self.set_flag('locale', lang)
                    return

class FileDictionary:
    def __init__(self, flags):
        self.flags = flags

    EXTENSIONS = {
        'container': {'.3gp', '.av1', '.avi', '.f4v', '.flv', '.m2ts', '.mkv', '.mp4', '.mpg', '.mov', '.mpeg', '.ogg',
                      '.ogm', '.ogv', '.ts', '.webm', '.wmv'},

        'video': {'.264', '.265', '.avc', '.h264', '.h265', '.hevc', '.ivf', '.m2v', '.mpv', '.obu', '.vc1', '.x264',
                  '.x265', '.m4v'},

        'audio': {'.aac', '.ac3', '.caf', '.dts', '.dtshd', '.eac3', '.ec3', '.flac', '.m4a', '.mka', '.mlp', '.mp2',
                  '.mp3', '.mpa', '.opus', '.ra', '.thd', '.truehd', '.tta', '.wav', '.weba', '.webma', '.wma'},

        'subs': {'.ass', '.mks', '.srt', '.ssa', '.sub', '.sup'},

        'font': {'.otf', '.ttf'},

        'mkvtools_supported': {'.mka', '.mks', '.mkv', '.webm'},
    }
    EXTENSIONS['video'] = EXTENSIONS['container'].union(EXTENSIONS['video'])
    EXTENSIONS['audio'] = EXTENSIONS['container'].union(EXTENSIONS['audio'])

    KEYS = {
        'search_subsdir': ['надписи', 'sign', 'russiansub', 'russub', 'субтит', 'sub'],

        'skipdir': {'bonus', 'бонус', 'special', 'bdmenu', 'commentary', 'creditless', '__temp_files__',
                    'nc', 'nd', 'op', 'pv'},

        'skip_file': {'_merged_', '_cutted_', '_added_', '_replaced_', '_temp_'},

        'lang': {'rus': {'надписи', 'субтитры', 'russian', 'rus', 'ru'},
                 'eng': {'english', 'eng', 'en'},
                 },

        'signs': {'надписи', 'signs'},
    }

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

            if any(key in filepath.stem for key in cls.KEYS['skip_file']):
                continue

            if (search_name in filepath.stem or filepath.stem in search_name) and filepath.is_file() and filepath.suffix.lower() in extensions:
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

        if not self.video_list: #try find .mkv for processing linking
            self.audio_dict = self.subs_dict = self.font_list = {}
            self.video_list = __class__.find_ext_files(self.flags.flag("start_dir"), ".mkv")

class Merge(FileDictionary):
    def set_output_path(self):
        if self.out_pname or self.out_pname_tail:
            stem = f'{self.out_pname}{self.ind+1:0{len(str(self.video_list_len))}d}{self.out_pname_tail}'

        else:
            stem = self.video.stem
            stem += '_cutted_video' if self.mkv_cutted else '_merged_video' if self.mkv_linking else ''
            if self.audio_list:
                stem += '_replaced_audio' if self.audio_dir and self.flag('orig_audio') is None or not self.bool_flag('orig_audio') else '_added_audio'
            if self.subs_list:
                stem += '_replaced_subs' if self.subs_dir and self.flag('orig_subs') is None or not self.bool_flag('orig_subs') else '_added_subs'
            if self.font_list:
                stem += '_added_fonts' if self.orig_fonts else '_replaced_fonts'

        self.output = Path(self.flags.flag('save_dir')) / f'{stem}.mkv'

    def for_flag(self, key3, filepath=None, filegroup=None):
        flag = None
        flag_list = []
        if not filepath or not filegroup:
            filepath = self.filepath
            filegroup = self.filegroup
        keys2 = [str(filepath), filegroup, str(filepath.parent)]

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

                    elif key3 in self.flags.__class__.TYPES['bool']:
                        flag = not False in flag_list

                    elif key3 in self.flags.__class__.TYPES['str']:
                        flag = ""
                        for flg in flag_list:
                            if flg:
                                flag += flg

        if flag is None and key3 == "options":
            return []
        return flag

    def flag(self, key, filepath=None, filegroup=None):
        if not filepath or not filegroup:
            filepath = self.filepath
            filegroup = self.filegroup

        flag = self.for_flag(key, filepath, filegroup)
        if flag is None and filegroup == "video" and "orig_" in key:
            flag = self.for_flag(key.replace("orig_", ""), filepath, filegroup)
        if flag is None and key != "options":
            flag = self.flags.flag(key, default_if_missing=False)
        return flag

    def bool_flag(self, key, filepath=None, filegroup=None):
        if not filepath or not filegroup:
            filepath = self.filepath
            filegroup = self.filegroup
        flg1 = self.flag(key, filepath, filegroup)
        flg2 = self.flags.flag(key, not self.pro)

        for val in [True, False]:
            if self.pro and key in self.flags.__class__.STRICT_BOOL.get(val, {}):
                return val if flg1 is val or (flg1 is None and flg2 is val) else not val
        return False if flg1 is False or (flg1 is None and not flg2) else True

    def set_track_name(self):
        tname = ''
        if self.filegroup != 'video':
            tname = self.flag('tname')
        if not tname and self.filegroup == 'subs':
            tname = self.flags.for_flag('signs', 'tname')
        if not tname:
            tname = FileInfo.get_file_info(self.filepath, 'Name:', self.tid)
        if not tname and self.filegroup != 'video':
            tname = self.__class__.get_trackname(self.video, self.filepath)
        self.tname = tname if tname else ''
        return self.tname

    def set_track_lang(self):
        tlang = ''
        if self.filegroup != 'video':
            tlang = self.flag('tlang')
        if not tlang and self.filegroup == 'subs':
            tlang = self.flags.for_flag('signs', 'tlang')
        if not tlang:
            tlang = FileInfo.get_file_info(self.filepath, 'Language:', self.tid)
        if not tlang:
            for lang, keys in self.__class__.KEYS['lang'].items():
                if self.__class__.path_has_keyword(self.video, self.filepath, keys):
                    tlang = lang
                if self.__class__.path_has_keyword(Path(''), Path(self.tname), keys):
                    tlang = lang
        self.tlang = tlang if tlang else ''
        return self.tlang

    def is_signs(self):
        keys = self.__class__.KEYS['signs']
        if self.__class__.path_has_keyword(Path(''), Path(self.tname), keys):
            return True
        if self.__class__.path_has_keyword(self.video, self.filepath, keys):
            return True

    def set_files_info(self):
        tmp_info = {}
        filepaths = [self.video] + self.audio_list + self.subs_list
        self.matches = self.splitted.matching_keys if self.mkv_split else {}

        for ind, filepath in enumerate(filepaths):
            if ind < 1:
                filegroup = 'video'
            elif ind < 1 + len(self.audio_list):
                filegroup = 'audio'
            else:
                filegroup = 'subs'

            if filegroup == 'video' and self.mkv_split and self.splitted.extracted_orig:
                trackgroups = ['video']
            else:
                trackgroups = ['video', 'audio', 'subs']

            for trackgroup in trackgroups:
                for tid in FileInfo.get_track_type_tids(filepath, trackgroup):
                    self.filepath, self.filegroup, self.tid = self.matches.get(str(filepath), [filepath, filegroup, tid])

                    if trackgroup != 'video':
                        self.info.setdefault(str(filepath), {}).setdefault(tid, {})['tname'] = self.set_track_name()
                        self.info.setdefault(str(filepath), {}).setdefault(tid, {})['tlang'] = self.set_track_lang()

                    if trackgroup == 'subs' and self.is_signs():
                        trackgroup = 'signs'
                    self.info.setdefault(str(filepath), {}).setdefault(trackgroup, []).append(tid)
                    self.info.setdefault('trackgroup', {}).setdefault(trackgroup, {}).setdefault(str(filepath), []).append(tid)

                    if trackgroup == 'signs' and filegroup == 'subs':
                        filegroup = 'signs'
                    self.info[str(filepath)]['filegroup'] = filegroup
                    if not filepath in tmp_info.setdefault('filegroup', {}).setdefault(filegroup, []):
                        tmp_info['filegroup'][filegroup].append(filepath)

        return tmp_info

    def get_sort_key(self, filepath, filegroup, tids=[]):
        self.filepath, self.filegroup = [filepath, filegroup]
        f_force = self.flag('forced')
        f_default = self.flag('default')
        f_enabled = self.flag('enabled')
        flag_order = {True: 0, None: 1, False: 2}

        flag_sort = (flag_order.get(f_force, 1), flag_order.get(f_default, 1), flag_order.get(f_enabled, 1))

        langs = set()
        for tid in tids:
            if self.info.get(str(filepath), {}).get(tid, {}).get('tlang', ''):
                langs.add(self.info[str(filepath)][tid]['tlang'])

        if self.locale in langs:
            lang_sort = 0  # self.locale first
            if not self.info.get('exists_locale_audio', False) and any(tid in self.info.get(str(filepath), {}).get('audio', []) for tid in tids):
                self.info['exists_locale_audio'] = True
        elif langs and not langs - {'jpn'}:
            lang_sort = 3  # 'jpn' latest
        elif langs:
            lang_sort = 2  # other lang
        else:
            lang_sort = 1  # undefined lang

        signs_sort = 0 if self.info.get(str(filepath), {}).get('signs', []) else 1

        return (flag_sort[0], flag_sort[1], flag_sort[2], lang_sort, signs_sort)

    def set_files_order(self, tmp_info):
        for filegroup in ['video', 'audio', 'signs', 'subs']:
            sorted_files = sorted(
                tmp_info['filegroup'].get(filegroup, []),
                key=lambda filepath: self.get_sort_key(filepath, filegroup, self.info.get(str(filepath), {}).get(filegroup, []))
            )
            self.info.setdefault('filegroup', {}).setdefault(filegroup, []).extend(sorted_files)
            self.info.setdefault('filepaths', []).extend(sorted_files)

    def set_tracks_order(self):
        tids_with_filepaths = []
        order_str = ''
        for trackgroup in ['video', 'audio', 'signs', 'subs']:
            tids_with_filepaths = []
            for filepath in self.info['filepaths']:
                tids_for_file = self.info.get(str(filepath), {}).get(trackgroup, [])
                for tid in tids_for_file:
                    tids_with_filepaths.append((tid, filepath))

            sorted_tids_with_filepaths = sorted(
                tids_with_filepaths,
                key=lambda item: self.get_sort_key(item[1], trackgroup, tids=[item[0]])
            )

            order = []
            for tid, filepath in sorted_tids_with_filepaths:
                fid = self.info['filepaths'].index(filepath)
                order.append((fid, tid))
                order_str = order_str + f'{fid}:{tid},'
            self.info.setdefault('t_order', {})[trackgroup] = tuple(order)
        self.info['t_order']['all_str'] = order_str[:-1]

    def set_merge_info_orders(self):
        self.set_files_order(self.set_files_info())
        self.set_tracks_order()

    def get_common_part_command(self):
        part = []
        self.fid += 1

        if not self.bool_flag('video'):
            part.append("--no-video")
        if not self.bool_flag('global_tags'):
            part.append("--no-global-tags")
        if not self.bool_flag('chapters'):
            part.append("--no-chapters")
        return part + self.for_flag('options')

    def get_part_command_for_video(self):
        part = []
        self.filepath, self.filegroup = [self.video, 'video']

        if self.audio_dir and self.audio_list and self.flag('orig_audio') is None or not self.bool_flag('orig_audio'):
            part.append("--no-audio")
        if self.subs_dir and self.subs_list and self.flag('orig_subs') is None or not self.bool_flag('orig_subs'):
            part.append("--no-subtitles")
        if self.orig_font_list or not self.orig_fonts:
            part.append("--no-attachments")
        return part + self.get_common_part_command()

    def get_part_command_for_file(self, filepath):
        part = []
        self.filepath = filepath
        if self.mkv_split and str(self.filepath) in self.splitted.matching_keys:
            self.filepath, self.filegroup, self.tid = self.splitted.matching_keys[str(self.filepath)]

        if self.filegroup != 'video' and not self.bool_flag('audio'):
            part.append('--no-audio')
        if self.filegroup != 'video' and not self.bool_flag('subs'):
            part.append('--no-subtitles')
        if not self.bool_flag('fonts'):
            part.append('--no-attachments')
        return part + self.get_common_part_command()

    def get_value_force_def_en(self, key):
        if self.trackgroup == 'signs' and key == 'forced' and self.flags.flag('forced_signs'):
            lim = self.flags.flag('lim_forced_signs')
        else:
            lim = self.flags.flag(f'lim_{key}_ttype')

        cnt = self.info.setdefault('cnt', {}).setdefault(key, {}).setdefault(self.trackgroup, 0)
        strict = 1 if key == 'forced' else 0
        force = self.flag(key)

        if cnt >= lim:
            value = 0
        elif force:
            value = 1
        elif key == 'forced' and self.trackgroup == 'signs' and self.flags.flag('forced_signs'):
            value = 1
        elif key == 'default' and self.trackgroup == 'subs' and self.info.get('exists_locale_audio', False):
            value = 0
        elif force is None and not strict and self.flags.flag(key):
            value = 1
        else:
            value = 0

        if value:
            self.info['cnt'][key][self.trackgroup] += 1

        return '' if value else ':0'

    def set_tids_flags_pcommand(self):
        for self.trackgroup in ['video', 'audio', 'signs', 'subs']:
            for fid, tid in self.info['t_order'].get(self.trackgroup, ()):
                part = []
                cmd = self.info['cmd'][fid]
                position = self.info.setdefault('position', {}).setdefault(fid, 0)
                filepath = self.info['filepaths'][fid]
                filegroup = self.info[str(filepath)]['filegroup']
                self.filepath, self.filegroup, *_ = self.matches.get(str(filepath), [filepath, filegroup])

                if self.bool_flag('forceds'):
                    val = self.get_value_force_def_en('forced')
                    part.extend(['--forced-display-flag', f'{tid}{val}'])

                if self.bool_flag('defaults'):
                    val = self.get_value_force_def_en('default')
                    part.extend(['--default-track-flag', f'{tid}{val}'])

                if self.bool_flag('enableds'):
                    val = self.get_value_force_def_en('enabled')
                    part.extend(['--track-enabled-flag', f'{tid}{val}'])

                if self.filegroup != 'video' or self.filegroup == 'video' and self.mkv_split and self.splitted.extracted_orig:
                    if self.bool_flag('tnames'):
                        val = self.info.get(str(filepath), {}).get(tid, {}).get('tname', '')
                        if val:
                            part.extend(['--track-name', f'{tid}:{val}'])
                    if self.bool_flag('tlangs'):
                        val = self.info.get(str(filepath), {}).get(tid, {}).get('tlang', '')
                        if val:
                            part.extend(['--language', f'{tid}:{val}'])

                cmd[position:position] = part
                self.info['position'][fid] += len(part)

    def get_merge_command(self):
        self.info = {}
        command = [str(Tools.mkvmerge), "-o", str(self.output)]
        self.set_merge_info_orders()

        if self.bool_flag('t_orders', self.video, 'video'):
            command.extend(['--track-order', self.info['t_order']['all_str']])

        self.fid = 0
        cmd = self.info.setdefault('cmd', {}).setdefault(self.fid, [])
        part = self.get_part_command_for_video()
        cmd.extend(part + [str(self.merge_video_list[0])])
        for video in self.merge_video_list[1:]:
            cmd.extend(part + [f'+{str(video)}'])

        for self.filegroup in ['audio', 'signs', 'subs']:
            for filepath in self.info['filegroup'].get(self.filegroup, []):
                cmd = self.info['cmd'].setdefault(self.fid, [])
                cmd.extend(self.get_part_command_for_file(filepath) + [str(filepath)])

        self.set_tids_flags_pcommand()
        for fid, cmd in self.info['cmd'].items():
            command.extend(cmd)

        for font in self.merge_font_list:
            command.extend(self.for_flag('options', font, 'fonts') + ['--attach-file', str(font)])

        command.extend(['--chapters', str(self.chapters)]) if self.chapters else None

        return command

    def processing_error_warning_merge(self, command_out, lmsg):
        cleaned_out = ''.join(command_out.split()).lower()
        last_line_out = command_out.splitlines()[-1]
        cleaned_lline_out = ''.join(last_line_out.split()).lower()

        if not self.setted_cp1251 and "textsubtitletrackcontainsinvalid8-bitcharacters" in cleaned_out:
            print("Invalid 8-bit characters in subs file!")
            for line in command_out.splitlines():
                if line.startswith("Warning") and "invalid 8-bit characters" in line:
                    filename_match = re.search(r"'(/[^']+)'", line)
                    filename = filename_match.group(1) if filename_match else None
                    filepath = TypeConverter.str_to_path(filename)

                    tid_match = re.search(r"track (\d+)", line)
                    tid = tid_match.group(1) if tid_match else None
                    if filepath and tid is not None:
                        self.flags.set_for_flag('options', ['--sub-charset', f'{tid}:windows-1251'], str(filepath))
                        self.setted_cp1251 = True

            if self.setted_cp1251:
                print("Trying to generate with windows-1251 coding.")
                self.execute_merge()
                return

        if not cleaned_lline_out.startswith("error"):
            print(lmsg)

            if "thecodec'sprivatedatadoesnotmatch" in cleaned_out:
                print('Attention! The generated video file maybe corrupted because video parts have mismatched codec parameters.')
                if not self.rm_linking:
                    print('Trying to generate another cutted version of the video without external video parts.')
                    self.splitted.processing_codec_error()
                    self.mkv_cutted = self.rm_linking = True
                    self.output = Path(str(self.output).replace('_merged_', '_cutted_'))
                    self.sort_orig_fonts(), self.execute_merge()

        else:
            if "containschapterswhoseformatwasnotrecognized" in cleaned_lline_out:
                print(f"{last_line_out}\nTrying to generate without chapters.")
                self.flags.set_for_flag('chapters', False, str(self.video))
                self.execute_merge()

            elif "nospaceleft" in cleaned_lline_out:
                if self.output.exists():
                    self.output.unlink()
                print(f"Error writing file!\nPlease re-run the script with other save directory.")
                self.delete_temp_files()

            else:
                if self.output.exists():
                    self.output.unlink()
                print(f"Error executing the command!\n{last_line_out}\nExiting the script.")
                self.delete_temp_files()

    def execute_merge(self):
        command = self.get_merge_command()

        print(f"\nGenerating a merged video file using mkvmerge. Executing the following command: \n{TypeConverter.command_to_print_str(command)}")
        lmsg = f"The command was executed successfully. The generated video file was saved to:\n{str(self.output)}"

        command_out = CommandExecutor.get_stdout(command, exit_after_error=False)
        if self.bool_flag('extended_log'):
            print(command_out) if not isinstance(command_out, tuple) else print(command_out[0])

        if not isinstance(command_out, tuple):
            print(lmsg)
        else:
            command_out = command_out[0]
            self.processing_error_warning_merge(command_out, lmsg)

    def set_common_merge_vars(self):
        self.locale = self.flags.flag('locale')
        self.video_list_len = len(self.video_list)
        self.out_pname = self.flags.flag("out_pname")
        self.out_pname_tail = self.flags.flag("out_pname_tail")
        self.splitted_info = {}
        self.temp_dir = Path(self.flags.flag("save_dir")) / f'__temp_files__.{str(uuid.uuid4())[:8]}'
        self.orig_font_dir = Path(self.temp_dir) / "orig_fonts"
        self.for_priority = self.flags.flag("for_priority")
        self.lim_gen = self.flags.flag("lim_gen")
        self.count_gen = 0
        self.count_gen_before = 0

        self.start_range = self.flags.flag("range_gen")[0]
        self.end_range = self.flags.flag("range_gen")[1]
        if self.start_range > 0:
            self.start_range = self.start_range - 1
            self.end_range = self.end_range - 1

    def get_merge_file_list(self, filegroup, filelist):
        filepath_list = []
        if self.flags.flag(filegroup):
            for filepath in filelist:
                if self.for_flag('files', filepath, filegroup) is not False:
                    filepath_list.append(filepath)
        return filepath_list

    def set_files_merge_vars(self):
        self.mkv_linking = self.mkv_cutted = self.mkv_split = self.rm_linking = self.setted_cp1251 = False
        self.pro = self.flag('pro')
        self.orig_fonts = self.bool_flag('orig_fonts')
        self.orig_font_list = []
        self.matching_keys = {}
        self.add_video_cmd = self.chapters = ''

        self.audio_list = self.get_merge_file_list("audio", self.audio_dict.get(str(self.video), []))
        self.subs_list = self.get_merge_file_list("subs", self.subs_dict.get(str(self.video), []))
        self.merge_font_list = self.get_merge_file_list("fonts", self.font_list)

    def sort_orig_fonts(self):
        if not self.bool_flag('sort_orig_fonts'):
            return

        if self.orig_font_dir.exists():
            shutil.rmtree(self.orig_font_dir)

        for filepath in self.merge_video_list + self.subs_list:
            if filepath.suffix in self.__class__.EXTENSIONS['mkvtools_supported']:
                names = []
                command = [str(Tools.mkvmerge), '-i', str(filepath)]
                for line in CommandExecutor.get_stdout(command, rm=self.delete_temp_files).splitlines():
                    match = re.search(r"file name '(.+?)'", line)
                    if match:
                        name = match.group(1)
                        names.append(name)

                command = [str(Tools.mkvextract), str(filepath), 'attachments']
                for ind, name in enumerate(names, start=1):
                    font = Path(self.orig_font_dir) / name
                    command.append(f'{ind}:{str(font)}')
                if len(command) > 3:
                    CommandExecutor.execute(command, rm=self.delete_temp_files)

        self.orig_font_list = self.__class__.find_ext_files(self.orig_font_dir, self.__class__.EXTENSIONS['font'])
        if self.orig_font_list:
            ext = self.get_merge_file_list('fonts', self.font_list)
            self.merge_font_list = self.__class__.rm_repeat_sort_fonts(ext + self.orig_font_list)

    def delete_temp_files(self, exit=True):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        if exit:
            sys.exit(1)

    def merge_all_files(self):
        self.set_common_merge_vars()

        for self.ind, self.video in enumerate(self.video_list[self.start_range:], start=self.start_range):
            self.filepath, self.filegroup = self.video, 'video'
            if self.count_gen >= self.lim_gen or self.ind > self.end_range:
                break
            if self.for_flag('files') is False:
                continue

            self.merge_video_list = [self.video]
            self.set_files_merge_vars()

            if self.video.suffix == ".mkv":
                self.splitted = SplittedMKV(self)
                self.mkv_linking = self.splitted.mkv_has_segment_linking()
                self.mkv_cutted = bool(self.splitted.skip)
                self.mkv_split = self.mkv_linking or self.mkv_cutted

                if all(not x for x in [self.mkv_split, self.audio_list, self.subs_list, self.merge_font_list]):
                    continue #skip video if not exist segment linking, external audio, subs or font

            self.set_output_path()
            if self.output.exists():
                self.count_gen_before += 1
                continue

            if self.mkv_split:
                self.splitted.processing_segments()

            self.sort_orig_fonts()
            self.execute_merge()
            self.count_gen += 1

        self.delete_temp_files(exit=False)

class SplittedMKV:
    def __init__(self, merge_instance):
        self.merge = merge_instance
        self.segments, self.matching_keys = {}, {}
        self.audio_list = self.merge.audio_list.copy()
        self.subs_list = self.merge.subs_list.copy()
        self.retimed_audio, self.retimed_subs = [], []
        self.skip = set()

    ACCEPT_OFFSETS = {'video': timedelta(milliseconds=5000),
                      'audio': timedelta(milliseconds=100)}

    def processing_codec_error(self):
        self.add_skips(linking=True)
        self.indexes[:] = [x for x in self.indexes if x not in self.skip]
        self.segments_vid[:] = [x for x in self.segments_vid if not (self.segments_inds[str(x)] & self.skip)]
        self.fill_retimed_audio(), self.fill_retimed_subs()
        self.generate_new_chapters() if self.merge.chapters else None

    def set_video_source(self, exit_if_none=False):
        self.info = self.merge.splitted_info.setdefault(self.uid, {})

        if not self.uid:
            self.source = self.merge.video
        else:
            self.source = self.info.get('source', None)
            if not self.source:
                for video in reversed(self.merge.__class__.find_ext_files(self.merge.video.parent, '.mkv')):
                    if FileInfo.get_file_info(video, 'Segment UID:').lower() == self.uid:
                        self.source = self.info['source'] = video
                        break

        if self.source:
            return self.source

        msg_tail = '. Please move this file to the video directory and re-run the script.' if exit_if_none else ' and has been skipped.'
        print(f"Video file with UID '{self.uid}' not found in the video directory '{str(self.merge.video.parent)}'."
              f"\nThis file is a segment of the linked video '{str(self.merge.video)}'{msg_tail}")

        if exit_if_none:
            self.merge.delete_temp_files()

        else: #add all uid segments in self.skip
            for ind, uid in enumerate(self.uids[self.ind:], start=self.ind):
                if uid == self.uid:
                    self.skip.add(ind)
            self.merge.splitted_info.setdefault('skip', set()).add(self.uid)

    def duration(self, key='max'):
        if self.info.setdefault('duration', {}).get(key, None):
            return self.info['duration'][key]

        durations = []
        for ttype in ['v', 'a']: #If audio > video, non-video audio is playback. If subs > video, non-video subs is not playback
            command = [Tools.ffprobe, '-v', 'quiet', '-select_streams', f'{ttype}', '-read_intervals', '99999999999']
            command += ['-show_entries', 'frame=pts_time', '-of', 'csv', str(self.source)] #time will decrease to last I frame
            for line in reversed(CommandExecutor.get_stdout(command, rm=self.merge.delete_temp_files).splitlines()):
                k = 'video' if ttype == 'v' else 'audio'
                td = self.info['duration'][k] = timedelta(seconds=float(line.split(',')[1]))
                durations.append(td)
                break
        self.info['duration']['max'] = max(durations)
        return self.info['duration'][key]

    def correct_chapters_times(self):
        if any(td is None for td in self.chap_starts + self.chap_ends):
            lengths = {}
            for ind, self.uid in enumerate(self.uids):
                start = self.chap_starts[ind] if self.chap_starts[ind] is not None else lengths.get(self.uid, timedelta(0))
                end = self.chap_ends[ind]

                if not end:
                    for temp_ind, time in enumerate(self.chap_starts[ind+1:], start=ind+1):
                        if time and self.uid == self.uids[temp_ind]:
                            end = time
                            break

                if not end:
                    self.set_video_source(exit_if_none=True)
                    end = self.duration()

                self.chap_starts[ind] = start
                self.chap_ends[ind] = end
                lengths[self.uid] = lengths.get(self.uid, timedelta(0)) + end

        for ind, self.uid in enumerate(self.uids):
            if self.set_video_source() and self.chap_ends[ind] > self.duration():
                self.chap_ends[ind] = self.duration() #real playback <= video or audio track duration

    def get_times_i_frames(self, td, offset_search):
        times = []
        command = [Tools.ffprobe, '-v', 'quiet', '-select_streams', f'v:{self.tid}', '-read_intervals', f'{td.total_seconds()}%+{str(offset_search)}']
        command += ['-show_entries', 'frame=pict_type,pts_time', '-of', 'csv', str(self.source)]
        for line in CommandExecutor.get_stdout(command, rm=self.merge.delete_temp_files).splitlines():
            if not 'I' in line: continue
            times.append(timedelta(seconds=float(line.split(',')[1])))
        return times

    def set_video_ind_end(self):
        for ind, uid in enumerate(self.uids[self.ind:], start=self.ind):
            if uid == self.uid and ind not in self.skip:
                self.ind_end = ind

            elif uid == self.uid:
                self.splitted = True
                break

            elif uid != self.uid and ind not in self.skip:
                if not self.splitted:
                    for uid in self.uids[ind:]:
                        if uid == self.uid:
                            self.splitted = True
                            break
                break

    def set_video_split_times(self):
        self.start = self.end = None
        self.set_video_ind_end()
        start, end = self.chap_starts[self.ind], self.chap_ends[self.ind_end]

        if start + abs(end - self.duration('video')) < self.strict:
            return True

        elif not self.uid and self.info.get('end', None) and abs(start - self.info['end']) < self.strict:
            self.start = self.info['end']

        temp = []
        for td in [start, end]:
            if td == start and self.start:
                temp.append(self.start)
                continue
            elif td == end and self.end:
                temp.append(self.end)
                continue

            times = self.get_times_i_frames(td, '0.000001')
            times.append(self.info['duration']['video'])
            times.extend(self.get_times_i_frames(td, 2*(td - times[0])))

            offset = timedelta(seconds=99999)
            for t in times:
                if abs(td - t) < offset:
                    time, offset = t, abs(td - t)
            temp.append(time)
        self.start, self.end = temp
        if not self.uid:
            self.info['end'] = self.end

    def set_segment_info(self, mkvmerge_stdout):
        duration = None
        timestamps = re.findall(r'Timestamp used in split decision: (\d{2}:\d{2}:\d{2}\.\d{9})', mkvmerge_stdout)
        if len(timestamps) == 2:
            self.defacto_start = TypeConverter.str_to_timedelta(timestamps[0])
            self.defacto_end = TypeConverter.str_to_timedelta(timestamps[1])

        elif len(timestamps) == 1:
            timestamp = TypeConverter.str_to_timedelta(timestamps[0])
            if self.start > timedelta(0): #timestamp for start
                self.defacto_start = timestamp
                duration = FileInfo.get_file_info(self.segment, 'Duration:')
                self.defacto_end = self.defacto_start + duration
            else:
                self.defacto_start = timedelta(0)
                self.defacto_end = timestamp

        else:
            self.defacto_start = timedelta(0)
            self.defacto_end = duration = FileInfo.get_file_info(self.segment, 'Duration:')

        self.offset_start = self.defacto_start - self.start
        self.offset_end = timedelta(0) if duration and self.defacto_end <= self.end else self.defacto_end - self.end #real play <= track duration
        self.length = self.defacto_end - self.defacto_start

    def split_file(self, repeat=True):
        command = [str(Tools.mkvmerge), '-o', str(self.segment), '--split', f'parts:{self.start}-{self.end}', '--no-global-tags', '--no-chapters', '--no-subtitles']
        command.append('--no-attachments') if not self.merge.orig_fonts else None
        command.append('--no-audio') if self.file_type == 'video' else command.append('--no-video')
        command.extend([f'--{self.file_type}-tracks', f'{self.tid}']) if self.tid is not None else None
        command.append(str(self.source))

        if self.merge.bool_flag('extended_log'):
            print(f"Extracting a segment of the {self.file_type} track from the file '{str(self.source)}'. Executing the following command:")
            print(TypeConverter.command_to_print_str(command))
        self.set_segment_info(CommandExecutor.get_stdout(command, rm=self.merge.delete_temp_files))

        if repeat and any(td > self.__class__.ACCEPT_OFFSETS[self.file_type] for td in [self.offset_start, self.offset_end]):
            old_start, old_end = self.start, self.defacto_end - self.offset_end
            self.start = self.start - self.offset_start if self.start - self.offset_start > timedelta(0) else self.start
            self.end = self.end - self.offset_end

            self.split_file(repeat=False)
            self.offset_start = self.defacto_start - old_start
            self.offset_end = self.defacto_end - old_end

    def set_video_segment_td(self):
        self.segment = Path(self.merge.temp_dir) / f'video_segment_{self.ind}_{self.uid}.mkv'
        info = self.merge.splitted_info.setdefault(self.segment, {}) if self.uid else {}

        if self.set_video_split_times():
            self.defacto_start, self.defacto_end = timedelta(0), self.duration('video')
            self.segment = self.source

        elif info.get('end', None) and abs(info['start'] - self.start) + abs(info['end'] - self.end) < self.strict:
            self.defacto_start, self.defacto_end = info['start'], info['end']

        elif all(not self.uids[ind] or self.uids[ind] in self.skip for ind in range(0, len(self.uids))):
            self.defacto_start, self.defacto_end = self.start, self.end
            self.segment = self.source

        else:
            self.split_file(repeat=False)
            if self.uid:
                info['start'], info['end'] = self.defacto_start, self.defacto_end

    def set_video_segment_info(self):
        self.set_video_segment_td()
        self.segments_vid.append(self.segment)
        self.segments_times.append([self.defacto_start, self.defacto_end])
        self.segments_inds.setdefault(str(self.segment), set()).update([self.ind, self.ind_end])

        for ind in range(self.ind, self.ind_end + 1):
            if ind in self.skip:
                continue
            self.indexes.append(ind)
            self.sources[ind] = self.source

            if ind == self.ind:
                self.starts[ind] = self.defacto_start
                self.offsets_start[ind] = self.defacto_start - self.chap_starts[ind]
            else:
                self.offsets_start[ind] = timedelta(0)

            if ind == self.ind_end:
                self.ends[ind] = self.defacto_end
                self.offsets_end[ind] = self.defacto_end - self.chap_ends[ind]
            else:
                for temp_ind, uid in enumerate(self.uids[ind+1:]):
                    if uid == self.uid:
                        next_uid_start = self.chap_starts[temp_ind]
                        break
                self.offsets_end[ind] = self.chap_ends[ind] - next_uid_start
            self.lengths[ind] = self.ends[ind] - self.starts[ind]

    def fill_video_segments(self):
        self.file_type = 'video'
        vid = self.segments['video'] = {}
        self.indexes = vid['indexes'] = []
        self.segments_vid, self.segments_times = vid['segments'], vid['segments_times'] = [], []
        self.segments_inds = vid['segments_inds'] = {}
        self.sources, self.lengths = vid['sources'], vid['lengths'] = {}, {}
        self.starts, self.ends = vid['starts'], vid['ends'] = self.chap_starts.copy(), self.chap_ends.copy()
        self.offsets_start, self.offsets_end = vid['offsets_start'], vid['offsets_end'] = {}, {}

        self.splitted = self.extracted_orig = False
        self.strict = self.__class__.ACCEPT_OFFSETS['video']
        tids = FileInfo.get_track_type_tids(self.merge.video, 'video')
        self.tid = tids[0]
        self.ind_end = -1
        for self.ind, self.uid in enumerate(self.uids):
            if self.ind <= self.ind_end or self.ind in self.skip or not self.set_video_source():
                continue
            self.set_video_segment_info()

        if self.splitted:
            options = ['--video-tracks', f'{self.tid}'] if len(tids) > 1 else []
            if all(not self.uids[ind] for ind in self.indexes):
                self.segments_vid[:] = [self.merge.video]
                str_times = ''
                for times in self.segments_times:
                    start = TypeConverter.timedelta_to_str(times[0], hours_place=2, decimal_place=6)
                    end = TypeConverter.timedelta_to_str(times[1], 2, 6)
                    str_times += f',+{start}-{end}' if str_times else f'{start}-{end}'
                options.extend(['--split', f'parts:{str_times}'])
            else:
                self.extracted_orig = True

            self.merge.flags.set_for_flag('options', options, str(self.merge.video)) if options else None

        if self.extracted_orig or len(self.segments_vid) > 1 and self.merge.bool_flag('force_retiming'):
            self.extracted_orig = True
            for flg in ['audio', 'subs']:
                self.merge.flags.set_for_flag(flg, False, str(self.merge.video))

    def merge_file_segments(self, segments):
        command = [str(Tools.mkvmerge), '-o', str(self.retimed)]
        command.append(segments[0])
        for segment in segments[1:]:
            command.append(f'+{str(segment)}')

        if self.merge.bool_flag('extended_log'):
            print(f'Merging retimed {self.file_type} track segments. Executing the following command:')
            print(TypeConverter.command_to_print_str(command))
        CommandExecutor.execute(command, rm=self.merge.delete_temp_files)

    def set_matching_keys(self, filepath, filegroup):
        self.matching_keys[str(self.retimed)] = [filepath, filegroup, self.tid]

    def get_segments_orig_audio(self):
        segments, lengths = [], {}
        for ind in self.indexes:
            self.start, self.end = self.starts[ind], self.ends[ind]
            offset = lengths.setdefault('audio', timedelta(0)) - lengths.setdefault('video', timedelta(0))
            self.start = self.start + offset if self.start + offset >= timedelta(0) else self.start

            self.segment = Path(self.merge.temp_dir) / 'orig_audio' / f'audio_{self.audio_cnt}_segment_{ind}.mka'
            self.source = self.sources[ind]
            self.split_file()
            segments.append(self.segment)

            lengths['video'] += self.lengths[ind]
            lengths['audio'] += self.length
        return segments

    def get_uid_lengths(self):
        lengths = {'uid': {'chapters': timedelta(0), 'defacto': timedelta(0)},
                   'nonuid': {'chapters': timedelta(0), 'defacto': timedelta(0)}}

        for ind in range(0, self.ind):
            key1 = 'uid' if self.uids[ind] == self.uids[self.ind] else 'nonuid'
            lengths[key1]['chapters'] += self.chap_ends[ind] - self.chap_starts[ind]
            if ind in self.indexes:
                lengths[key1]['defacto'] += self.ends[ind] - self.starts[ind]
        for key1 in ['uid', 'nonuid']:
            lengths[key1]['offset'] = lengths[key1]['defacto'] - lengths[key1]['chapters']
        return lengths

    def get_segments_ext_audio(self):
        segments, lengths = [], {}
        for self.ind in self.indexes:
            nonuid_length = self.get_uid_lengths()['nonuid']['chapters']
            offset = lengths.setdefault('audio', timedelta(0)) - lengths.setdefault('video', timedelta(0))

            self.start = self.starts[self.ind] + nonuid_length + offset if self.starts[self.ind] + nonuid_length + offset >= timedelta(0) else self.starts[self.ind] + nonuid_length
            self.end = self.ends[self.ind] + nonuid_length

            self.segment = Path(self.merge.temp_dir) / 'ext_audio' / self.source.parent.name / f'audio_{self.audio_cnt}_segment_{self.ind}.mka'
            self.split_file()
            segments.append(self.segment)

            lengths['video'] += self.lengths[self.ind]
            lengths['audio'] += self.length
        return segments

    def fill_retimed_audio(self):
        self.retimed_audio[:] = []
        temp = []
        self.file_type = 'audio'
        self.audio_cnt = 0
        if self.orig_audio and self.extracted_orig:
            for self.tid in FileInfo.get_track_type_tids(self.merge.video, 'audio'):
                temp.append([self.merge.video, 'video', self.tid])
        for self.source in self.audio_list:
            for self.tid in FileInfo.get_track_type_tids(self.source, 'audio'):
                temp.append([self.source, 'audio', self.tid])

        for tmp in temp:
            self.source, filepath, filegroup, self.tid = tmp[0], *tmp
            segments = self.get_segments_orig_audio() if filegroup == 'video' else self.get_segments_ext_audio()

            self.retimed = Path(self.segment.parent) / f'audio_{self.audio_cnt}.mka'
            self.merge_file_segments(segments)
            self.retimed_audio.append(self.retimed)
            self.set_matching_keys(filepath, filegroup)
            self.audio_cnt += 1

    def extract_track(self):
        command = [str(Tools.mkvextract), 'tracks', str(self.source), f'{self.tid}:{str(self.segment)}']
        if self.merge.bool_flag('extended_log'):
            print(f"Extracting subtitles track {self.tid} from the file '{str(self.source)}'. Executing the command:")
            print(TypeConverter.command_to_print_str(command))
        CommandExecutor.execute(command, rm=self.merge.delete_temp_files)

    def write_subs_segment_lines(self, file, lines):
        for line in lines:
            if line.startswith('Dialogue:'):
                parts = line.split(',')
                start = TypeConverter.str_to_timedelta(parts[1].strip())
                end = TypeConverter.str_to_timedelta(parts[2].strip())

                if start < self.start and end < self.start or start > self.end and end > self.end:
                    continue #skip non-segment lines

                else: #retime and write
                    new_start = TypeConverter.timedelta_to_str(start + self.offset)
                    new_end = TypeConverter.timedelta_to_str(end + self.offset)
                    line = f"{parts[0]},{new_start},{new_end},{','.join(parts[3:])}"
                    file.write(line)

    def add_retimed_orig_subs(self):
        lines = {}
        for ind in self.indexes:
            if lines.get(self.uids[ind], []):
                continue
            self.source = self.sources[ind]
            self.segment = Path(self.merge.temp_dir) / 'orig_subs' / f'subs_{self.subs_cnt}_segment_{ind}.ass'
            self.extract_track()
            with open(self.segment, 'r', encoding='utf-8') as file:
                lines[self.uids[ind]] = file.readlines()

        self.retimed = Path(self.segment.parent) / f'subs_{self.subs_cnt}.ass'
        with open(self.retimed, 'w', encoding='utf-8') as file:
            for line in lines[self.uids[self.indexes[0]]]:
                if line.startswith('Dialogue:'): break
                file.write(line) #save lines before dialogues

            for self.ind in self.indexes:
                lengths = self.get_uid_lengths()
                self.offset = lengths['nonuid']['defacto'] + lengths['uid']['offset'] - self.offsets_start[self.ind]
                uid, self.start, self.end = self.uids[self.ind], self.starts[self.ind], self.ends[self.ind]
                self.write_subs_segment_lines(file, lines[uid])

        self.retimed_subs.append(self.retimed)
        self.set_matching_keys(self.merge.video, 'video')
        self.subs_cnt += 1

    def add_retimed_ext_subs(self):
        with open(self.retimed, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        with open(self.retimed, 'w', encoding='utf-8') as file:
            for line in lines:
                if line.startswith('Dialogue:'): break
                file.write(line) #save lines before dialogues

            for self.ind in self.indexes:
                lengths = self.get_uid_lengths()
                self.offset = lengths['nonuid']['offset'] + lengths['uid']['offset'] - self.offsets_start[self.ind]
                self.start, self.end = self.starts[self.ind] + lengths['nonuid']['chapters'], self.ends[self.ind] + lengths['nonuid']['chapters']
                self.write_subs_segment_lines(file, lines)

        self.retimed_subs.append(self.retimed)
        self.set_matching_keys(self.source, 'subs')
        self.subs_cnt += 1

    def fill_retimed_subs(self):
        self.retimed_subs[:] = []
        self.subs_cnt = 0

        if self.orig_subs and self.extracted_orig:
            for self.tid in FileInfo.get_track_type_tids(self.merge.video, 'subtitles (SubStationAlpha)'):
                self.add_retimed_orig_subs()

        for self.source in self.subs_list:
            tids = []
            if self.source.suffix in self.merge.__class__.EXTENSIONS['mkvtools_supported']:
                tids = FileInfo.get_track_type_tids(self.source, 'subtitles (SubStationAlpha)')

            if self.source.suffix == '.ass':
                self.retimed = Path(self.merge.temp_dir) / 'ext_subs' / self.source.parent.name / f'subs_{self.subs_cnt}.ass'
                self.retimed.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(self.source, self.retimed)
                self.add_retimed_ext_subs()

            elif tids:
                for self.tid in tids:
                    self.retimed = Path(self.merge.temp_dir) / 'ext_subs' / self.source.parent.name / f'subs_{self.subs_cnt}.ass'
                    self.extract_track(self.retimed)
                    self.add_retimed_ext_subs()

            else:
                print(f"Skip subtitles file '{str(self.source)}'! \nThese subtitles need to be retimed because the video file is splitted. Retime is only possible for SubStationAlpha tracks (.ass).")

    def generate_new_chapters(self):
        self.merge.chapters = Path(self.merge.temp_dir) / 'new_chapters.xml'

        root = ET.Element('Chapters')
        edition = ET.SubElement(root, 'EditionEntry')
        ET.SubElement(edition, 'EditionFlagOrdered').text = '1'
        ET.SubElement(edition, 'EditionFlagDefault').text = '1'
        ET.SubElement(edition, 'EditionFlagHidden').text = '0'
        length = timedelta(0)
        for ind in self.indexes:
            start, end, name = length, self.lengths[ind] + length, self.names[ind]
            chapter = ET.SubElement(edition, 'ChapterAtom')
            ET.SubElement(chapter, 'ChapterTimeStart').text = TypeConverter.timedelta_to_str(start, hours_place=2, decimal_place=6)
            ET.SubElement(chapter, 'ChapterTimeEnd').text = TypeConverter.timedelta_to_str(end, 2, 6)
            if name:
                chapter_display = ET.SubElement(chapter, 'ChapterDisplay')
                ET.SubElement(chapter_display, 'ChapterString').text = name
            length += end - start

        xml_str = ET.tostring(root, encoding='utf-8', method='xml')
        parsed_xml = minidom.parseString(xml_str)
        pretty_xml_str = parsed_xml.toprettyxml(indent='  ')
        with open(self.merge.chapters, 'w', encoding='utf-8') as file:
            file.write(pretty_xml_str)

    def processing_segments(self):
        if not Tools.ffprobe_installed(exit_if_none=False):
            self.merge.delete_temp_files()
        self.merge.splitted_info[str(self.merge.video)] = {}
        self.correct_chapters_times()
        self.orig_audio, self.orig_subs = self.merge.bool_flag('orig_audio'), self.merge.bool_flag('orig_subs')

        self.fill_video_segments(), self.fill_retimed_audio(), self.fill_retimed_subs()
        self.merge.merge_video_list, self.merge.audio_list, self.merge.subs_list = self.segments_vid, self.retimed_audio, self.retimed_subs
        if self.merge.bool_flag('chapters'):
            self.merge.flags.set_for_flag('chapters', False, str(self.merge.video))
            self.generate_new_chapters()

    def add_skips(self, linking=False):
        names = set()
        for flag in ['opening', 'ending']:
            if not self.merge.bool_flag(flag):
                names.add(flag)
                for flg_short, flg_long in self.merge.flags.__class__.MATCHINGS['full'].items():
                    names.add(flg_short) if flg_long == flag else None
        names.update({name.lower() for name in self.merge.flags.flag('rm_chapters')})

        rm_linking = linking or not self.merge.bool_flag('linking')
        ind = 0
        for name in self.names:
            uid = self.uids[ind]
            if name.lower() in names or rm_linking and uid or uid and uid in self.merge.splitted_info.setdefault('skip', set()):
                self.skip.add(ind)
            ind += 1

    def set_chapters_info(self, chapters):
        chap = self.segments['chapters'] = {}
        self.uids = chap['uids'] = []
        self.chap_starts, self.chap_ends = chap['starts'], chap['ends'] = [], []
        self.names = chap['names'] = []

        try:
            tree = ET.parse(chapters)
        except Exception:
            return
        root = tree.getroot()

        for atom in root.findall('.//ChapterAtom'):
            uid = atom.find('ChapterSegmentUID')
            uid = uid.text.lower() if uid is not None else ''
            self.uids.append(uid)

            start = atom.find('ChapterTimeStart')
            start = TypeConverter.str_to_timedelta(start.text) if start is not None else None
            self.chap_starts.append(start)

            end = atom.find('ChapterTimeEnd')
            end = TypeConverter.str_to_timedelta(end.text) if end is not None else None
            self.chap_ends.append(end)

            name = atom.find('.//ChapterDisplay/ChapterString')
            name = name.text if name is not None else ''
            self.names.append(name)

    def mkv_has_segment_linking(self):
        chapters = Path(self.merge.temp_dir) / 'chapters.xml'
        if chapters.exists(): chapters.unlink()
        CommandExecutor.execute([str(Tools.mkvextract), str(self.merge.video), 'chapters', str(chapters)], rm=self.merge.delete_temp_files)

        self.set_chapters_info(chapters), self.add_skips()
        return True if any(uid for uid in self.uids) else False

def main():
    flags = Flags()
    flags.processing_sys_argv()
    if flags.flag("lim_gen") == 0:
        print("A new video can't be generated because the limit-generate set to 0.")
        sys.exit(0)

    Tools.set_tools_paths()
    if flags.flag('rm_chapters'):
        Tools.ffprobe_installed()

    print(f"Trying to generate a new video in the save directory '{str(flags.flag("save_dir"))}' using files from the start directory '{str(flags.flag("start_dir"))}'.")

    merge = Merge(flags)
    merge.find_all_files()
    lmsg = f"Files for generating a new video not found. Checked the directory '{str(flags.flag("start_dir"))}', its subdirectories and {flags.flag("lim_search_up")} directories up."

    if not merge.video_list:
        print(lmsg)
        sys.exit(0)
    elif flags.flag("range_gen")[0] > len(merge.video_list):
        print(f"A new video can't be generated because the start range-generate exceeds the number of video files.")
        sys.exit(0)

    merge.merge_all_files()

    if merge.count_gen_before:
        print(f"{merge.count_gen_before} video files in the save directory '{str(flags.flag("save_dir"))}' had generated names before the current run of the script. Generation for these files has been skipped.")

    if merge.count_gen:
        print(f"\nThe generate was executed successfully. {merge.count_gen} video files were generated in the directory '{str(flags.flag("save_dir"))}'")
    else:
        print(lmsg)

if __name__ == "__main__":
    main()
