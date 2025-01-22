# generate-video-with-these-files

## Script for adding external tracks to a video, merging, and retiming tracks of linked mkv (mkv segment linking) video

## How to use

1. [Download](https://github.com/nujievik/generate-video-with-these-files-script/releases) the executable file (.exe) for Windows x64 or the packaged script set (.pyz).
2. If you use the **script set**, install [dependencies](https://github.com/nujievik/generate-video-with-these-files-script?tab=readme-ov-file#dependencies).
3. Run it in the directory containing the videos or external files.

The default behavior can be changed by configuring the [configuration file](https://github.com/nujievik/generate-video-with-these-files-script?tab=readme-ov-file#configuration-file) or by passing [command-line arguments](https://github.com/nujievik/generate-video-with-these-files-script?tab=readme-ov-file#command-line-arguments). In particular, you don't need to copy the script into the directory with the files, but you can simply pass the directory as an argument:

```
generate-video-with-these-files.exe "directory with files"
```

## Dependencies

- [Python](https://www.python.org/downloads/)
- [Chardet](https://github.com/chardet/chardet)
- [MKVToolNix](https://mkvtoolnix.download/)
- [FFprobe](https://ffmpeg.org/download.html) (for splitted MKV)

## License

- **Own Code**: [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html)
- **Python**: [PSF License](https://www.python.org/psf/license/)
- **Chardet**: [GNU Lesser General Public License v2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **MKVToolNix**: [GNU General Public License v2.0](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
- **FFprobe** (part of FFmpeg): [GNU Lesser General Public License v2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)

## Description

The project includes a set of Python scripts that use custom components **Python**, **MKVToolNix**, and **FFmpeg**. The source code of the scripts is available in the repository.

For convenience, a compiled executable file (.exe) for Windows x64 is available in the [Releases](https://github.com/nujievik/generate-video-with-these-files-script/releases) section. For other systems, a packaged script set (.pyz) is available.

The executable file for Windows contains all the necessary components for the operation:
- The set of scripts from the repository, compiled using **PyInstaller**.
- Precompiled components of **MKVToolNix** (sourced from the official [MKVToolNix website](https://mkvtoolnix.download/downloads.html#windows)).
- Precompiled version of **FFprobe** (sourced from BtbN's FFmpeg win64-gpl release on [GitHub](https://github.com/BtbN/FFmpeg-Builds/releases)).

The packaged script set (.pyz) is assembled using **zipapp** and requires the installation of [dependencies](https://github.com/nujievik/generate-video-with-these-files-script?tab=readme-ov-file#dependencies).

## Functionality

- Works on Windows, GNU/Linux. Should work on macOS and BSD.
- Creates a merged MKV container without re-encoding tracks.
- Finds files for merging by partial filename match with the video name.
- Finds files in subdirectories of the video directory.
- Merges linked (mkv segment linking) video.
- Allows you to trim a portion of an MKV video (for MKVs with chapters).
- Retimes audio and subtitles for linked or trimmed videos to prevent desynchronization.
- Sets the encoding for subtitles that are not recognized in UTF.
- Names audio and subtitle tracks based on their file name tail OR the directory name. (The original name, if present, is preserved).
- Sets the language of audio and subtitle tracks based on keywords in the file paths.
- Sets the system locale language as the priority for track sorting.
  - Supports English and Russian. If not specified, defaults to Russian.
- Sorts tracks in the output file across multiple levels. (Sorting in a previous level does not affect results):
  - Video > Audio > Titles > Subtitles
  - Forced (True > None > False, where True and False are manually set values, and None means not set).
  - Default (True > None > False)
  - Enabled (True > None > False)
  - Localized track > undefined languages > other languages > Japanese track
  - Track from file with titles > without titles
- Sets Forced, Default, and Enabled flags based on track sorting. By default:
  - Forced is disabled for all tracks.
  - Default is enabled for one track of each type (the first in the sorting order). If the localized audio track is set to default or if the default is set to the audio track in the subtitle language, then the default for subtitles is disabled.
  - Enabled is enabled for all tracks.
- Adds fonts for subtitles to the container.
- Sorts all fonts by name, including those already present in the container before merging.
- Skips unrecognized by mkvmerge files and chapters.
- Allows significant changes to default behavior by adding call arguments.
- Supports any arguments supported by `mkvmerge`.
- Allows setting merge arguments for all files in the directory, for file groups (video, audio, titles, subtitles), and for individual files.

## Default mode

- The starting directory and saving directory are the current working directory.
- Files to merge are searched in subdirectories of the starting directory and up to 3 parent directories.
- If the script starts in the video directory, all found tracks are ADDED to the original.
- If started in an external files directory, the original tracks are REPLACED with the found ones.
- If started in an external audio directory, it looks for one external subtitle file (priority is given to subtitle tracks).
- If started in an external subtitle directory, the original audio is preserved.
- Track-order, Forced, Default, Enabled, Track-name, and Language flags are set.
- Tracks are sorted with local tracks given priority.
- The output file is named after the video, with a suffix indicating what was done (_added_audio, _replaced_subs, etc.)
- Linked video is split into parts, written to disk, and then the parts are combined into a single video.

## Working with linked video

By default, linked video is written to disk in parts first and then merged into a complete video. This process effectively uses twice the disk space of the final video size.

To reduce disk resource usage, you can exclude linked video segments (typically openings and endings). In this case, intermediate parts will not be written, and the final video will be generated directly. This can be done using the flag:
```
python generate-video-with-these-files.pyz -linking
```

## Configuration file

- It should be located in the current working directory.
  
- It has a lower priority than **command-line arguments**. If a flag value is specified both in the configuration file and in the command-line argument, the latter will take precedence.

- It supports all the **command-line arguments** listed below.

- Syntax examples and commented default values for all flags are listed in the [configuration file](https://github.com/nujievik/generate-video-with-these-files-script/blob/main/config-generate-video-with-these-files.ini).

- To change a flag value in the **configuration file**, uncomment the line and modify the value on the right.

## Argument remapping mode

This mode is activated by passing call arguments. Unspecified arguments remain at default values. The generated `mkvmerge` command includes all flags that are not manually disabled.

## Pro mode

This mode is activated by passing the `+pro` argument. It disables the sorting of fonts already in the video container and creates a clean `mkvmerge` command without flags (`mkvmerge -o outfile file1 file2 file3`). It can be combined with argument remapping, including re-including flags that were removed.

## Command-line arguments

- You can pass any number of arguments.

- If an argument is not recognized, the execution is stopped.

- Arguments can be passed with different syntax.
  - Prefixes like `+`, `-`, `--`, `--no-`, and `--save-` are allowed for supported arguments outside `-for=`.
  - For unsupported arguments outside `-for=`, use the [syntax of mkvmerge options](https://mkvtoolnix.download/doc/mkvmerge.html).
 
### Version
`--version` displays the current version of the program and exits.

### Startdir and savedir

- Absolute or relative paths can be specified. `startdir` should be specified before `savedir` if `savedir` is passed without the `-save-dir=` key.

- `"start directory"` or `-start-dir="start dir"` sets the start directory.

- `-save-dir="save directory"` sets the save directory.

### Text arguments

- Text must be specified after `=`. For example, `-tname="track name"`.

- `-locale=` sets the priority language for track sorting.

- `-out-pname=` and `-out-pname-tail=` set the start and end of the output file name, respectively. Between them, the file number is automatically added, and the extension `.mkv` is appended.

- `-tname=` sets the track name.

- `-lang=` sets the track language.

### Limits

- Requires specifying a non-negative integer after `=`. For example, `-lim-gen=1`.

- `-lim-search-up=` sets the number of parent directories in which video files are searched for merging (for the script running from an external files directory).

- `-lim-gen=` sets the maximum number of generated videos.

- `-lim-forced-ttype=` sets the maximum number of forced tracks per type (video, audio, titles, subtitles). Default is 0. If increased, also include `+forced`.

- `-lim-forced-signs=` sets the limit for forced titles. Default is 1. To enable forced titles, also include `+forced-signs`.

- `-lim-default-ttype=` sets the limit for default tracks per type. Default is 1.

- `-lim-enabled-ttype=` sets the limit for enabled tracks per type. By default, there is no limit, and all tracks are enabled.

### Generation range

- Requires specifying one or two non-negative integers with a separator. The separator can be `-`, `,`, `:`. For example, `-range-gen=2-8`.

- `-range-gen=` sets the generation range for video files. Only videos with corresponding external tracks are considered (if they exist). Videos are taken in alphabetical order.

### Removing chapters

- `-rm-chapters=op,ed,prologue,preview` removes the specified video segments listed in the argument (for MKVs with chapters).

### TrueFalse arguments

- TrueFalse arguments are set to True or False depending on the symbol before the argument: `+` for True and `-` for False. Also, if the argument starts with `--no`, the value is False, in all other cases, it is True. Specifically, True is set if the argument is called with a double dash `--` without `no`.

- `+pro` activates Pro mode (generates a clean mkvmerge command without flags).

- `+extended-log` activates extended logging.

- `-search-dirs` disables file search in directories above the starting directory. It performs a recursive search in subdirectories of the starting directory.

- `-sub-charsets` disables setting the encoding for subtitles that are not recognized in UTF.

- `-linking` removes external parts of linked video.

- `-opening` removes the video segment containing the opening (for MKVs with chapters).

- `-ending` removes the video segment containing the ending (for MKVs with chapters).

- `-force-retiming` disables the retiming of the original audio and subtitles for the linked video if the main part of the video is not split.

- `-global-tags` disables copying of global tags.

- `-chapters` disables copying of chapters.

- `-video` disables copying of video tracks.

- `-audio` without `-for=` before it disables adding external audio files and audio tracks. With the `-for="target" -audio` argument, it disables copying audio tracks from the specified files.

- `-orig-audio` disables copying audio tracks from the video file.

- `-subs` behaves similarly to `-audio`, but for subtitles.

- `-orig-subs` disables copying subtitle tracks from the video file.

- `-fonts` disables adding external fonts.

- `-orig-fonts` disables copying fonts from the video file.

- `-sort-orig-fonts` disables sorting of fonts already in the video container in alphabetical order.

- `-fonts` and `-attachments` arguments are equivalent.

- `-tnames` disables adding tracknames flags to the mkvmerge command.

- `-tlangs` disables adding language flags.

- `-forceds` disables adding forced flags.

- `+forced` enables the forced flag. For a specific file, if `-for=` is set, or for all files if not specified. The number of positive values is limited by `-lim-forced-ttype=`.

- `+forced-signs` sets a positive forced flag for signs. The number of positive values is limited by `-lim-forced-signs=`, with a default of 1.

- `-defaults` disables adding default flags.

- `+default` sets a positive default flag. The number of positive values is limited by `-lim-default-ttype=`, with a default of 1.

- `-enableds` disables adding enabled flags.

- `-enabled` sets a negative enabled flag. By default, all tracks have a positive enabled flag, and there is no limit on the number set by `-lim-enabled-ttype=`.

- `-no-fonts` disables fonts if any fonts were added before.


### For arguments

- To specify paths in `-for=`, you need to use absolute paths.

- `-for-priority=` sets the priority of flags specified through `-for=`.
  - `file_first` is the default - if flags are set for a file, the flags for the group and directory of that file are ignored.
  - `dir_first` is the opposite - if set for a directory, the flags for the file are ignored.
  - `mix` is the mixed mode, which considers all flags related to the file, group, and directory of the file.

- `-for="target"` sets flags for a specific file, group of files (video, audio, subs, signs), or for a directory. It supports:
  - TrueFalse flags of the script
  - Text options `-lang=` and `-tname=`
  - Any flags supported by mkvmerge. For mkvmerge flags, you need to follow the [syntax of mkvmerge options](https://mkvtoolnix.download/doc/mkvmerge.html).

- `-for="target" -files` skips the specified files.

- `-for="target" -options=[--video-tracks, 0, --audio-tracks, 1]` is a special flag for recording unsupported arguments outside of -for. Without explicitly specifying options, you can simply write `-for="target" --video-tracks 0 --audio-tracks 1`.

- `-for=all` or `-for=` without specifying a path or group returns the input arguments to the common ones.


## Examples of changing default behavior

All examples are written for the Python script. If you are running the `.exe`, just replace `python generate-video-with-these-files.pyz` to `generate-video-with-these-files.exe`.

### Disable file search in directories above
It will search for files recursively in subdirectories of the starting directory.
```
python generate-video-with-these-files.pyz -search-dirs
```

### Change start directory
```
python generate-video-with-these-files.pyz -start-dir="path to the directory"
```

### Change save directory
```
python generate-video-with-these-files.pyz -save-dir="path to the directory"
```

### Get a clean command 'mkvmerge -o outfile file1 file2 file3'
```
python generate-video-with-these-files.pyz +pro
```

### Set priority language for sorting tracks
```
python generate-video-with-these-files.pyz -locale=eng
```

### Set default track
```
python generate-video-with-these-files.pyz -for="target" +default
```

### Set track names
For external tracks:
```
python generate-video-with-these-files.pyz -tname="track name"
```

For video:
```
python generate-video-with-these-files.pyz -for=video --track-name trackID:"track name"
```

### Set track languages
For external tracks:
```
python generate-video-with-these-files.pyz -tlang=language
```

For video:
```
python generate-video-with-these-files.pyz -for=video --language trackID:language
```


### Set positive forced flags
Only for subtitles (default limit is 1, you may omit it):
```
python generate-video-with-these-files.pyz +forced-signs +lim-forced-signs=1
```

For tracks of each type:
```
python generate-video-with-these-files.pyz +forced +lim-forced-ttype=1
```

### Set negative default flags
```
python generate-video-with-these-files.pyz -lim-default-ttype=0
```

### Set negative enabled flags
```
python generate-video-with-these-files.pyz -lim-enabled-ttype=0
```

### Change output file names
Set the prefix of the name. The file number and the `.mkv` extension will be added at the end:
```
python generate-video-with-these-files.pyz -out-pname="prefix "
```

Set the suffix of the name after the file number. The `.mkv` extension will be automatically added at the end:
```
python generate-video-with-these-files.pyz -out-pname-tail=" suffix"
```

#### Example to set name 'Death Note - episodeNumber (BDRip 1920x1080).mkv'
```
python generate-video-with-these-files.pyz -out-pname="Death Note - " -out-pname-tail=" (BDRip 1920x1080)"
```

### Add only external audio / subtitles / fonts
Audio:
```
python generate-video-with-these-files.pyz +audio -subs -fonts
```

Subtitles:
```
python generate-video-with-these-files.pyz +subs -audio -fonts
```

Fonts:
```
python generate-video-with-these-files.pyz +fonts -audio -subs
```

### Add tracks to original ones, not replace them
```
python generate-video-with-these-files.pyz +orig-audio +orig-subs
```

### Replace original tracks with external ones, not add them
```
python generate-video-with-these-files.pyz -orig-audio -orig-subs -orig-fonts
```

### Remove all audio / subtitles / fonts tracks
Audio:
```
python generate-video-with-these-files.pyz -audio -orig-audio
```

Subtitles:
```
python generate-video-with-these-files.pyz -no-subs -orig-subs
```

Fonts:
```
python generate-video-with-these-files.pyz -fonts -orig-fonts
```

### Process only a part of the files
Via generation range.
In this case, files will only be created for the specified range.
```
python generate-video-with-these-files.pyz -range-gen=8-10
```


Via generation limit.
In this case, a specified number of files will be created. Files will be iterated from the beginning. If the output file exists, the generation counter will not increase, and the next file will be taken.
```
python generate-video-with-these-files.pyz -lim-gen=4
```

### Disable track sorting
```
python generate-video-with-these-files.pyz -track-orders
```

### Disable sorting of existing fonts in the video container
```
python generate-video-with-these-files.pyz -sort-orig-fons
```

### Remove chapters and global tags from files
```
python generate-video-with-these-files.pyz -chapters -global-tags
```

### Do not set track names
```
python generate-video-with-these-files.pyz -tnames
```

### Do not set track languages
```
python generate-video-with-these-files.pyz -tlangs
```

### Disable automatic flag setting for forced, default, enabled, trackname, and language
```
python generate-video-with-these-files.pyz -forceds -defaults -enableds -tnames -tlangs
```

### Do not add files from a specific directory
```
python generate-video-with-these-files.pyz -for="path to the directory" -files
```


## Long and short versions of arguments

- A negative value can be written either with a `-` or with `--no-`, and a positive value can be written with a `+` or `--save-`. For example, `-chapters` is equivalent to `--no-chapters`, and `+chapters` is equivalent to `--save-chapters` or simply `--chapters`. The double dash without `no` gives a positive value.

- All arguments can be written in a longer and more understandable form. The following abbreviations are used (words in arguments listed with `|` are interchangeable):
```
'pro-mode' | 'pro' 
'directory' | 'dir'
'directories' | 'dirs'
'output' | 'out' 
'partname' | 'pname' 
'limit' | 'lim' 
'generate' | 'gen' 
'save_' | '' 
'no_' | '' 
'add_' | '' 
'original' | 'orig' 
'subtitles' | 'subs' 
'attachments' | 'fonts' 
'language' | 'lang' 
'track_orders' | 't_orders' 
'track_type' | 'ttype' 
'trackname' | 'tname' 
'track_lang' | 'lang' 
'tlang' | 'lang'
'remove' | 'rm'
```


-----


# generate-video-with-these-files

## Cкрипт для добавления внешних дорожек в видео, объединения и ретайминга дорожек линкованного mkv видео

## Как этим пользоваться

1. [Скачайте](https://github.com/nujievik/generate-video-with-these-files-script/releases) исполняемый файл (.exe) для Windows x64 или универсальный набор скриптов (.pyz).
2. Если используете **набор скриптов**, установите [зависимости](https://github.com/nujievik/generate-video-with-these-files-script/tree/main?tab=readme-ov-file#%D0%B7%D0%B0%D0%B2%D0%B8%D1%81%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D0%B8).
3. Запустите в директории, содержащей видео или внешние файлы.

Поведение по умолчанию можно изменить, настроив [файл конфигурации](https://github.com/nujievik/generate-video-with-these-files-script/tree/main?tab=readme-ov-file#%D0%A4%D0%B0%D0%B9%D0%BB-%D0%BA%D0%BE%D0%BD%D1%84%D0%B8%D0%B3%D1%83%D1%80%D0%B0%D1%86%D0%B8%D0%B8) или передав [аргументы командной строки](https://github.com/nujievik/generate-video-with-these-files-script/tree/main?tab=readme-ov-file#%D0%90%D1%80%D0%B3%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B-%D0%BA%D0%BE%D0%BC%D0%B0%D0%BD%D0%B4%D0%BD%D0%BE%D0%B9-%D1%81%D1%82%D1%80%D0%BE%D0%BA%D0%B8). В частности, можно не копировать скрипт в директорию с файлами, а просто передать ее в качестве аргумента:
```
generate-video-with-these-files.exe "директория с файлами"
```

## Зависимости

- [Python](https://www.python.org/downloads/)
- [Chardet](https://github.com/chardet/chardet)
- [MKVToolNix](https://mkvtoolnix.download/)
- [FFprobe](https://ffmpeg.org/download.html) (для разделенного MKV)

## Лицензия

- **Собственный код**: [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html)
- **Python**: [PSF License](https://www.python.org/psf/license/)
- **Chardet**: [GNU Lesser General Public License v2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **MKVToolNix**: [GNU General Public License v2.0](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
- **FFprobe** (часть FFmpeg): [GNU Lesser General Public License v2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)

## Описание

Проект включает набор Python-скриптов, которые используют пользовательские компоненты **Python**, **MKVToolNix** и **FFmpeg**. Исходный код скриптов доступен в репозитории.

Для удобства использования в разделе [Releases](https://github.com/nujievik/generate-video-with-these-files-script/releases) для Windows x64 доступен скомпилированный исполняемый файл (.exe). А для остальных систем - упакованный набор скриптов (.pyz).

Исполняемый файл для Windows содержит все необходимые для работы компоненты:
- Набор скриптов из репозитория, скомпилированный с помощью **PyInstaller**.
- Скомпилированные компоненты **MKVToolNix** (полученные с официального [сайта MKVToolNix](https://mkvtoolnix.download/downloads.html#windows)).
- Скомпилированную версию **FFprobe** (полученную из релиза FFmpeg win64-gpl от BtbN на [GitHub](https://github.com/BtbN/FFmpeg-Builds/releases)).

Упакованный набор скриптов (.pyz) собран с помощью **zipapp** и требует установки [зависимостей]((https://github.com/nujievik/generate-video-with-these-files-script/tree/main?tab=readme-ov-file#%D0%B7%D0%B0%D0%B2%D0%B8%D1%81%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D0%B8)).

## Функциональность

- Работает в Windows, GNU/Linux. Должен работать в macOS и BSD.
- Создает объединенный MKV контейнер без перекодирования дорожек.
- Находит файлы для объединения по частичному совпадению имени файла с именем видео.
- Находит файлы в поддиректориях директории видео.
- Объединяет линкованное (mkv segment linking) видео.
- Позволяет обрезать часть mkv видео (для mkv с chapters).
- Ретаймит аудио и субтитры для объединенного линкованного или обрезанного видео, чтобы не было рассинхрона.
- Выставляет кодировку для нераспознанных в UTF субтитров.
- Называет дорожки аудио и субтитров по хвосту их имени ИЛИ по имени директории. (Исходное название, если оно есть, копируется без изменений).
- Устанавливает язык дорожек аудио и субтитров по ключевым словам в пути к файлам.
- Устанавливает язык системной локали приоритетным для сортировки дорожек.
  - поддерживаются eng и rus. Если не определено - rus.
- Сортирует дорожки в выходном файле в несколько уровней. (Результат разбивки на группы в предыдущем уровне новая сортировка не меняет):
  - видео > аудио > надписи > субтитры
  - forced (True > None > False, где True и False - заданные вручную значения, а None - не задано).
  - default (True > None > False)
  - enabled (True > None > False)
  - локализованная дорожка > неопределенные языки > другие языки > японская дорожка
  - дорожка из файла с надписями > без надписей
- Проставляет Forced, Default, Enabled флаги на основании сортировки дорожек. По умолчанию:
  - forced для всех отключено
  - default включено для одной дорожки каждого типа (первой в сортировке). Если локализованная аудиодорожка установлена default или default установлена аудиорожка на языке субтитров, то default для субтитров выключено.
  - enabled для всех включено
- Добавляет шрифты для субтитров в контейнер.
- Сортирует все шрифты по имени. (В том числе уже имевшиеся в контейнере до объединения).
- Пропускает нераспознанные mkvmerge файлы и chapters.
- Позволяет значительно изменить поведение по умолчанию, добавив аргументы вызова.
- Поддерживает любые аргументы, поддерживаемые mkvmerge.
- Позволяет задать аргументы объединения для всех файлов в директории, для групп файлов (видео, аудио, надписи, субтитры) и для отдельных файлов.

## Режим по умолчанию

- Стартовая директория и директория сохранения - текущая рабочая директория.
- Файлы для объединения ищутся в поддиректориях стартовой директории и в 3 родительских директориях.
- Если старт в директории видео, все найденные дорожки ДОБАВЛЯЮТСЯ к исходным.
- Если старт в директории внешних файлов, исходные дорожки ЗАМЕНЯЮТСЯ найденными.
- Если старт в директории внешних аудио, ищется 1 штука внешних субтитров (приоритет поиск надписей).
- Если старт в директории внешних субтитров, оригинальное аудио сохраняется.
- Проставляются track-order, forced, default, enabled, track-name, language флаги.
- Сортируются дорожки с приоритетом локальных
- Имя выходного файла ставится имя видео + суффикс что сделано (_added_audio, _replaced_subs и т.п.)
- Линкованное видео разделяется на части, части записываются на диск и потом объединяются.

## Работа с линкованным видео

По умолчанию линкованное видео записывается на диск сначала по частям, потом из этих частей собирается целое видео. Фактически перезаписывается в 2 раза больший объем диска, чем весит итоговое видео. 

Чтобы снизить трату дискового ресурса, можно отрезать прилинкованные видео части (обычно это опенинг и эндинг). Тогда промежуточные части записываться не будут, будет сразу писаться итоговое видео. Сделать это можно с помощью флага:
```
python generate-video-with-these-files.pyz -linking
```

## Файл конфигурации

- Должен располагаться в текущей рабочей директории.

- Имеет более низкий приоритет над **аргументами командной строки**. При указании значения флага в файле конфигурации и в аргументе командной строки приоритет будет отдан последнему.

- Поддерживает все перечисленные ниже **аргументы командной строки**. 

- Примеры синтаксиса и закомментированные дефолтные значения всех флагов перечислены в [файле конфигурации](https://github.com/nujievik/generate-video-with-these-files-script/blob/main/config-generate-video-with-these-files.ini).

- Чтобы изменить значение флага в **файле конфигурации**, нужно раскомментировать строку и изменить значение справа.

## Режим переназначения аргументов

Активируется передачей аргументов вызова. Непереданные аргументы остаются на дефолтных значениях. Формируемая mkvmerge команда включает все неотключенные вручную флаги.

## PRO режим

Активируется передачей `+pro` аргумента. Отключает сортировку шрифтов для шрифтов в контейнере видео. Формирует чистую mkvmerge команду без флагов `mkvmerge -o outfile file1 file2 file3`. Можно комбинировать с режимом переназначения, в частности включать в команду убранные флаги.

## Аргументы командной строки

- Имеют приоритет над аргументами в **файле конфигурации**. При указании значения флага в файле конфигурации и в аргументе командной строки приоритет будет отдан последнему.

- Можно передать любое количество аргументов.

- Если аргумент не распознан, выполнение завершается.

- Аргументы можно передавать с разным синтаксисом. 
  - допустимы префиксы `+`, `-`, `--`, `--no-`, `--save-` для поддерживаемых вне `-for=` аргументов. 
  - для неподдерживаемых вне `-for=` нужно соблюдать [синтаксис опций mkvmerge](https://mkvtoolnix.download/doc/mkvmerge.html).

### Версия
`--version` выводит текущую версию программы и завершает работу.

### Стартдир и сейвдир

- Можно указывать как абсолютные так и относительные текущей рабочей директории пути. `стартдир` должен быть указан до `сейвдир`, если `сейвдир` передается без ключа `-save-dir=`.

- `"стартовая директория"` или `-start-dir="старт дир"` устанавливает стартовую директорию.

- `-save-dir="директория сохранения"` устанавливает директорию сохранения. 

### Текстовые

- Требуют указания текста после `=`. Например, `-tname="имя дорожки"`.

- `-locale=` устанавливает приоритетный язык для сортировки дорожек.

- `-out-pname=` и `out-pname-tail=` устанавливают начало и конец имени выходных файлов соответственно. Между ними автоматически проставляется номер файла, а в конце расширение .mkv.

- `-tname=` устанавливает имя дорожек.

- `-lang=` устанавливает язык дорожек.

### Лимиты

- Требуют указания целого неотрицательного числа после `=`. Например, `-lim-gen=1`.

- `-lim-search-up=` устанавливает количество родительских директорий в которых ищутся видеофайлы для объединения (для сценария запуска скрипта из директории внешних файлов).

- `-lim-gen=` устанавливает максимальное количество генерируемых видео.

- `-lim-forced-ttype=` устанавливает максимальное количество форсированных дорожек каждого типа (видео, аудио, надписи, субтитры). По умолчанию 0. При увеличении нужно также включить `+forced`.

- `-lim-forced-signs=` устанавливает лимит форсированных надписей. По умолчанию 1. Для включения forced для надписей нужно также включить `+forced-signs`.

- `-lim-default-ttype=` устанавливает лимит дефолтных дорожек каждого типа. По умолчанию 1.

- `-lim-enabled-ttype=` устанавливает лимит включенных дорожек каждого типа. По умолчанию нет лимита, все дорожки включены.

### Диапазон генерации

- Требует указания 1 или 2 целых неотрицательных чисел с разделителем. В качестве разделителя можно использовать `-`, `,`, `:`. Например, `-range-gen=2-8`.

- `-range-gen=` устанавливает диапазон генерации для видеофайлов. Берутся только видео, имеющие соответствующие внешние дорожки (если те существуют). Видео берутся в алфавитном порядке.

### Удаление глав

- `-rm-chapters=op,ed,prologue,preview` удаляет перечисленные через запятую части видео (для mkv с chapters).

### TrueFalse

- TrueFalse аргументы устанавливаются в True либо False в зависимости от символа перед аргументом `+` и `-` соответственно. Значение отрицательно также если аргумент начинается с `--no`, во всех остальных случаях оно положительно. В частности положительное значение устанавливается если аргумент вызывается с двойным дефисом `--`, за которым нет `no`.

- `+pro` активирует Pro режим (дает чистую команду mkvmerge без флагов).

- `+extended-log` активирует расширенный лог.

- `-search-dirs` отключает поиск файлов в директориях выше директории старта. Используется рекурсивный поиск в поддиректориях старта.

- `-sub-charsets` отключает выставление кодировки для нераспознанных в UTF субтитров.

- `-linking` удаляет внешние части линкованного видео.

- `-opening` удаляет часть видео с опенингом (для mkv с chapters).

-  `-ending` удаляет часть видео с эндингом (для mkv с chapters).

- `-force-retiming` отключает ретайминг оригинальных аудио и субтитров для линкованного видео, если основная часть видео не разделена.

- `-global-tags` отключает копирование глобальных тегов.

- `-chapters` отключает копирование глав.

- `-video` отключает копирование видеодорожек.

- `-audio` без аргумента `-for=` перед ним отключает добавление внешних аудиофайлов и аудиодорожек. С аргументом `-for="для чего" -audio` отключается копирование аудиодорожек из заданных файлов.

- `-orig-audio` отключает копирование аудиодорожек из видеофайла.

- `-subs` поведение аналогично `-audio`, но для субтитров.

- `-orig-subs` отключает копирование дорожек субтитров из видеофайла.

- `-fonts` отключает добавление внешних шрифтов.

- `-orig-fonts` отключает копирование шрифтов из видеофайла.

- `-sort-orig-fonts` отключает сортировку уже имеющихся в видеоконтейнере шрифтов в алфавитном порядке.

- `-fonts` и `-attachments` аргументы эквиваленты.

- `-tnames` отключает добавление флагов имен дорожек в команду mkvmerge.

- `-tlangs` отключает добавление флагов языков.

- `-forceds` отключает добавление флагов forced.

- `+forced` устанавливает положительное значение forced. Для конкретного файла если задан `-for=` или для всех если не задан. Количество положительных значений ограничено лимитом `-lim-forced-ttype=`, который по умолчанию 0.

- `+forced-signs` устанавливает положительное значение forced для надписей. Количество положительных значений ограничено `-lim-forced-signs=`, по умолчанию 1.

- `-defaults` отключает добавление default флагов в команду.

- `+default` устанавливает положительное значение default. Количество положительных значений ограничено `-lim-default-ttype=`, по умолчанию 1.

- `-enableds` отключает добавление enabled флагов в команду.

- `-enabled` устанавливает отрицательное значение enabled. По умолчанию всем дорожкам проставляется положительное enabled, а количество `-lim-enabled-ttype=` не ограничено.

### For аргументы

- Для указания путей в `-for=` нужно использовать абсолютные пути.

- `-for-priority=` устанавливает приоритет флагов заданных через `-for=`. 
  - `file_first` установлен по умолчанию - если заданы флаги для файла, то флаги для группы и директории этого файла не учитываются. 
  - `dir_first` зеркальное отражение, если задано для директории, для файла не учитываются. 
  - `mix` смешанный режим учитывает все флаги, относящиеся к файлу, группе и директории файла.

- `-for="для чего"` устанавливает флаги для конкретного файла, группы файлов (video, audio, subs, signs) или для директории. Поддерживает: 
  - TrueFalse флаги скрипта 
  - текстовые `-lang=` и `-tname=`
  - любые флаги, поддерживаемые mkvmerge. Для флагов mkvmerge нужно соблюдать [синтаксис опций mkvmerge](https://mkvtoolnix.download/doc/mkvmerge.html). 

- `-for="для чего" -files` пропускает заданные файлы.

- `-for="для чего" -options=[--video-tracks, 0, --audio-tracks, 1]` специальный флаг для записи неподдерживаемых вне `-for` аргументов. Без явного указания options можно просто писать `-for="для чего" --video-tracks 0 --audio-tracks 1"`

- `-for=all` или `-for=` без указания пути или группы возвращает ввод аргументов к общим.


## Примеры изменения поведения по умолчанию

Все примеры написаны для Python. Если вы запускаете `.exe` просто замените `python generate-video-with-these-files.pyz` на `generate-video-with-these-files.exe`

### Отключить поиск файлов в директориях выше
Будет искать файлы рекурсивно в поддиректориях директории старта
```
python generate-video-with-these-files.pyz -search-dirs
```

### Изменить директорию старта
```
python generate-video-with-these-files.pyz -start-dir="путь к директории"
```

### Изменить директорию сохранения
```
python generate-video-with-these-files.pyz -save-dir="путь к директории"
```

### Получить чистую команду 'mkvmerge -o outfile file1 file2 file3'
```
python generate-video-with-these-files.pyz +pro
```

### Установить приоритетный язык для сортировки дорожек
```
python generate-video-with-these-files.pyz -locale=eng
```

### Установить дорожку по умолчанию
```
python generate-video-with-these-files.pyz -for="для чего" +default
```

### Установить имя дорожек
Для внешних дорожек:
```
python generate-video-with-these-files.pyz -tname="имя дорожки"
```

Для видео:
```
python generate-video-with-these-files.pyz -for=video --track-name *IDдорожки*:"имя дорожки"
```

### Установить язык дорожек
Для внешних дорожек:
```
python generate-video-with-these-files.pyz -tlang=язык
```

Для видео:
```
python generate-video-with-these-files.pyz -for=video --language *IDдорожки*:язык
```

### Установить положительные forced
Только для надписей (по умолчанию лимит 1, можно не задавать):
```
python generate-video-with-these-files.pyz +forced-signs +lim-forced-signs=1
```

Для дорожек каждого типа:
```
python generate-video-with-these-files.pyz +forced +lim-forced-ttype=1
```

### Установить отрицательные default
```
python generate-video-with-these-files.pyz -lim-default-ttype=0
```

### Установить отрицательные enabled
```
python generate-video-with-these-files.pyz -lim-enabled-ttype=0
```

### Изменить имя выходных файлов
Установить начало имени. В конце будет добавлен номер файла и расширение .mkv.:
```
python generate-video-with-these-files.pyz -out-pname="prefix "
```
Установить хвост имени после номера файла. В конце автоматически добавится .mkv:
```
python generate-video-with-these-files.pyz -out-pname-tail=" suffix"
```

#### Пример установить имя 'Death Note - номерсерии (BDRip 1920x1080).mkv'
```
python generate-video-with-these-files.pyz -out-pname="Death Note - " -out-pname-tail=" (BDRip 1920x1080)"
```

### Добавить только внешние аудио / субтитры / шрифты
Аудио:
```
python generate-video-with-these-files.pyz +audio -subs -fonts
```
Субтитры:
```
python generate-video-with-these-files.pyz +subs -audio -fonts
```
Шрифты:
```
python generate-video-with-these-files.pyz +fonts -audio -subs
```

### Добавить дорожки к оригинальным, а не заменить оригинальные
```
python generate-video-with-these-files.pyz +orig-audio +orig-subs
```

### Заменить оригинальные дорожки внешними, а не добавить
```
python generate-video-with-these-files.pyz -orig-audio -orig-subs -orig-fonts
```

### Удалить все дорожки аудио / субтитров / все шрифты
Аудио:
```
python generate-video-with-these-files.pyz -audio -orig-audio
```
Субтитры:
```
python generate-video-with-these-files.pyz -no-subs -orig-subs
```
Шрифты:
```
python generate-video-with-these-files.pyz -fonts -orig-fonts
```

### Обработать только часть файлов
Через диапазон генерации.
В этом случае создаются файлы только для указанного диапазона.
```
python generate-video-with-these-files.pyz -range-gen=8-10
```

Через лимит генерации.
В этом случае создастся заданное количество файлов. Файлы перебираются с начала. Если выходной файл существует, счетчик генерации не увеличивается, берется следующий файл.
```
python generate-video-with-these-files.pyz -lim-gen=4
```

### Отключить сортировку дорожек
```
python generate-video-with-these-files.pyz -track-orders
```

### Отключить сортировку уже имеющихся в видеоконтейнере шрифтов
```
python generate-video-with-these-files.pyz -sort-orig-fons
```

### Удалить главы и теги из файлов
```
python generate-video-with-these-files.pyz -chapters -global-tags
```

### Не проставлять имена дорожек
```
python generate-video-with-these-files.pyz -tnames
```

### Не проставлять языки дорожек
```
python generate-video-with-these-files.pyz -tlangs
```

### Отключить автоматическое проставление флагов forced, default, enabled, trackname, language
```
python generate-video-with-these-files.pyz -forceds -defaults -enableds -tnames -tlangs
```

### Не добавлять файлы из определенной директории
```
`python generate-video-with-these-files.pyz -for="путь к директории" -files`
```


## Длинные и короткие версии аргументов

- Отрицательное значение можно записать как через `-` так и через `--no-`, а положительное через `+` либо `--save-`. Например, `-chapters` эквиваленто `--no-chapters`, а `+chapters` эквиваленто `--save-chapters` либо просто `--chapters`. Двойной дефис без `no` дает положительное значение.

- Все аргументы можно записать в более длинном и понятном виде. Применяются следующие сокращения (слова в аргументах, перечисленные через `|`, взаимозаменяемы):
```
'pro-mode' | 'pro'
'directory' | 'dir'
'directories' | 'dirs'
'output' | 'out'
'partname' | 'pname'
'limit' | 'lim'
'generate' | 'gen'
'save_' | ''
'no_' | ''
'add_' | ''
'original' | 'orig'
'subtitles' | 'subs'
'attachments' | 'fonts'
'language' | 'lang'
'track_orders' | 't_orders'
'track_type' | 'ttype'
'trackname' | 'tname'
'track_lang' | 'lang'
'tlang' | 'lang'
'remove' | 'rm'
```
