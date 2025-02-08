# merge-tracks-with-video

## Script for fast merging external tracks with video

## How to use

1. [Download](
https://github.com/nujievik/merge-tracks-with-video/releases) the
executable file (.exe) for Windows x64 or the packaged script set
(.pyz).
2. If you use the **script set**, install [dependencies](#dependencies).
3. Run it in the directory containing the videos or external tracks.

The default behavior can be changed by configuring the
[configuration file](#configuration-file) or by passing
[command-line arguments](#command-line-arguments). In particular, you
don't need to copy the script into the directory with the files, but
you can simply pass the directory as an argument:

```
merge-tracks-with-video.exe "directory with files"
```

## Dependencies

- [Chardet](https://github.com/chardet/chardet)
- [MKVToolNix](https://mkvtoolnix.download/)
- [Python](https://www.python.org/downloads/)
- [FFprobe](https://ffmpeg.org/download.html) (for splitted MKV)

## License

- **Own Code**: [GNU General Public License v3.0](
https://www.gnu.org/licenses/gpl-3.0.html)
- **Chardet**: [GNU Lesser General Public License v2.1](
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **MKVToolNix**: [GNU General Public License v2.0](
https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
- **Python**: [PSF License](https://www.python.org/psf/license/)
- **FFprobe** (part of FFmpeg):
[GNU Lesser General Public License v2.1](
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)

## Description

The project includes a set of Python scripts that use custom components
**Python**, **MKVToolNix**, and **FFmpeg**. The source code of the
scripts is available in the repository.

For convenience, a compiled executable file (.exe) for Windows x64 is
available in the [Releases](
https://github.com/nujievik/merge-tracks-with-video/releases) section.
For other systems, a packaged script set (.pyz) is available.

The executable file for Windows contains all the necessary components
for the operation:
- The set of scripts from the repository, compiled using 
**PyInstaller**.
- Precompiled components of **MKVToolNix** (sourced from the official
[MKVToolNix website](
https://mkvtoolnix.download/downloads.html#windows)).
- Precompiled version of **FFprobe** (sourced from BtbN's FFmpeg
win64-gpl release on [GitHub](
https://github.com/BtbN/FFmpeg-Builds/releases)).

The packaged script set (.pyz) is assembled using **zipapp** and
requires the installation of [dependencies](#dependencies).

## Functionality

- Works on Windows, GNU/Linux. Should work on macOS and BSD.
- Creates a merged MKV container without re-encoding tracks.
- Find files for merging:
  - by partial filename match with the video
  - in the parent directories of the start directory
  - in subdirectories of the video directory
- Merges tracks linked (mkv segment linking) video.
- Allows you to trim a portion of an MKV video (if MKV has chapters).
- Retimes audio and subtitles for linked or trimmed videos to prevent
desynchronization.
- Sets the encoding for subtitles that are not recognized in UTF.
- Sets the names of audio and subtitles tracks based on their file name
tail OR the directory name. (The original name, if present, is
preserved).
- Sets the language of audio and subtitle tracks based on keywords in
the file paths. (The original language preserved also).
- Sets the system locale language as the priority for track sorting and
applies it to the track sorting process.
- Sets Forced, Default, and Enabled flags based on track sorting.
- Adds fonts for subtitles to the container.
- Sorts all fonts by name, including those already present in the
container before merging.
- Skips unrecognized by mkvmerge files and chapters.
- Allows significant changes to default behavior by adding call
arguments.
- Supports any options supported by **mkvmerge**.
- Allows setting merge options for all files in the directory, for
file groups, and for individual files.

## Default mode

- The starting directory and saving directory are the current working
directory.
- Files to merge are searched for in up to 3 parent directories of the
starting directory and its subdirectories.
- If the starting directory in:
  - the video directory - all found tracks are ADDED to the original
  tracks
  - an external files directory - the original tracks are REPLACED with
  the found tracks
- If the starting directory in an:
  - external audio directory - it looks for one external subtitle file
  (priority is given to signs track)
  - external subtitles directory - the original audio is preserved
- Sorting tracks in the output file across multiple levels:
  - Video > Audio > Signs > Subtitles
  - Forced (True > None > False, where True and False are manually set
  values, and None means not set)
  - Default (True > None > False)
  - Enabled (True > None > False)
  - Localized track > undefined languages > other languages >
  Japanese track
  - Track from file with signs > track fro file without signs
- Sets Forced, Default, and Enabled flags based on track sorting:
  - Forced is disabled for all tracks
  - Default is enabled for one track of each type (the first in the
  sorting order). If the localized audio track is set to default or if
  the default is set to the audio track in the subtitle language, then
  the default for subtitles is disabled
  - Enabled is enabled for all tracks
- Track-order, Forced, Default, Enabled, Track-name, and Language
flags are set.
- The output file is named after the video, with a suffix indicating
what was done (_added_audio, _replaced_subs, etc.)
- Linked video is split into parts, written to disk, and then the parts
are combined into a single video.

## Working with linked video

By default, linked video is written to disk in parts first and then
merged into a complete video. This process effectively uses twice the
disk space of the final video size.

To reduce disk resource usage, you can exclude linked video segments
(typically openings and endings). In this case, intermediate parts will
not be written, and the final video will be generated directly. This
can be done using the flag:

```
python merge-tracks-with-video.pyz -linking
```

## Options reassignment mode

Activated by passing [command-line arguments](#command-line-arguments)
or configuring the [configuration file](#configuration-file). Options
not passed remain at their default values. The generated `mkvmerge`
command includes all options that have not been manually disabled.

## Pro mode

This mode is activated by passing the `+pro` argument. It disables the
sorting of fonts already in the video container and creates a clean
`mkvmerge` command without flags 
(`mkvmerge -o outfile file1 file2 file3`). It can be combined with
argument remapping, including re-including flags that were removed.

## Configuration file

- It should be located in the current working directory.
- It has a lower priority than **command-line arguments**. (If an
option value is specified both in the configuration file and in the
command-line argument, the latter will take priority).
- Syntax examples and commented default values for all options are
listed in the [configuration file](
https://github.com/nujievik/merge-tracks-with-video/blob/main/config-merge-tracks-with-video.ini).
- To change an option value, uncomment the line in the file and modify
the value on the right.

## Command-line arguments

- Take precedence over options in the **configuration file**. (If an
option value is specified both in the configuration file and in the
command-line argument, the latter will take priority).
- If an argument is not recognized, the execution is stopped.
- Arguments can be passed with different syntax.
  - Prefixes like `+`, `-`, `--`, `--no-`, and `--save-` are allowed
  for supported arguments outside `-target=`
  - For unsupported arguments outside `-target=`, use the 
  [syntax of mkvmerge options](
  https://mkvtoolnix.download/doc/mkvmerge.html)
  
## Options list
 
### Version

`--version` displays the current version of the program and exits.

### Startdir and Savedir

Absolute or relative paths can be specified. `startdir` should be
specified before `savedir` if `savedir` is passed without the
`-save-dir=` key.

- `"start directory"` or `-start-dir="start directory"` sets the start
directory.
- `-save-dir="save directory"` sets the save directory.

### Text options

Text must be specified after `=`. For example, `-tname="track name"`.

- `-locale=` sets the priority language for track sorting.
- `-out-pname=` and `-out-pname-tail=` set the start and end of the
output file name, respectively. Between them, the file number is
automatically added, and the extension `.mkv` is appended.
- `-tlang=` sets the track language.
- `-tname=` sets the track name.

### Limits

Requires specifying a non-negative integer after `=`. For example,
`-lim-gen=1`.

- `-lim-search-up=` sets the number of parent directories in which
video files are searched for merging (for the script running from an
external files directory).
- `-lim-gen=` sets the maximum number of generated videos.
- `-lim-forced-ttype=` sets the maximum number of forced tracks per
type (video, audio, titles, subtitles). Default is 0. If increased,
also include `+forced`.
- `-lim-forced-signs=` sets the limit for forced titles. Default is 1.
To enable forced titles, also include `+forced-signs`.
- `-lim-default-ttype=` sets the limit for default tracks per type.
Default is 1.
- `-lim-enabled-ttype=` sets the limit for enabled tracks per type.
By default, there is no limit, and all tracks are enabled.

### Generation range

Requires specifying one or two non-negative integers with a separator.
The separator can be `-`, `,`, `:`. For example, `-range-gen=2-8`.

- `-range-gen=` sets the generation range for video files. Only videos
with corresponding external tracks are considered (if they exist).
Videos are taken in alphabetical order.

### Removing chapters

`-rm-chapters=op,ed,prologue,preview` removes the specified video
segments listed in the argument (if MKV has chapters).

### Flags

Flags are set to True or False by passing the corresponding values.
For example, `-subtitles=False`.
For **command-line arguments**, you can set them using prefixes without
directly passing a value. The prefixes `+` and `-` correspond to True
and False, respectively. For example, `-subtitles`. The flag value is
also set to False if the argument is passed with the `--no-` prefix.
However, a double dash without `no` before it corresponds to True. For
instance, `--subtitles` sets it to True, while `--no-subtitles` sets it
to False.

- `+pro` activates Pro mode (generates a clean mkvmerge command without
arguments).
- `+verbose` activates verbose (extended logging).

- `-search-dirs` disables file search in directories above the starting
directory. (It performs a recursive search in subdirectories of the
starting directory).

- `-video` disables copying of video tracks.
- `-audio` disables adding external audio files.
- `-orig-audio` disables copying audio tracks from the video file.
- `-target="any target" -audio` disables copying audio tracks from the
specified files.
- `-subs` disables adding external subtitle files.
- `-orig-subs` disables copying subtitle tracks from the video file.
- `-target="any target" -subs` disables copying subtitle tracks from
the specified files.
- `-sub-charsets` disables setting the encoding for subtitles that are
not recognized in UTF.
- `-fonts` disables adding external fonts.
- `-orig-fonts` disables copying fonts from the video file.
- `-sort-orig-fonts` disables sorting of fonts already in the video
container in alphabetical order.

- `-chapters` disables copying of chapters.
- `-global-tags` disables copying of global tags.

- `-linking` removes external parts of linked video.
- `-opening` removes the video segment containing the opening (if MKV
has chapters).
- `-ending` removes the video segment containing the ending (if MKV has
chapters).
- `-force-retiming` disables the retiming of the original audio and
subtitles for the linked video if the main part of the video is not
split.

- `-track-orders` disables track sorting.

- `-tlangs` disables adding language flags.
- `-tnames` disables adding tracknames flags to the mkvmerge command.

- `-forceds` disables adding forced flags.
- `+forced` enables the forced flag. For a specific file, if `-target=`
is set, or for all files if not specified. The number of positive
values is limited by `-lim-forced-ttype=`.
- `+forced-signs` sets a positive forced flag for signs. The number of
positive values is limited by `-lim-forced-signs=`, with a default of 1.
- `-defaults` disables adding default flags.
- `+default` sets a positive default flag. The number of positive
values is limited by `-lim-default-ttype=`, with a default of 1.
- `-enableds` disables adding enabled flags.
- `-enabled` sets a negative enabled flag. By default, all tracks have
a positive enabled flag, and there is no limit on the number set by
`-lim-enabled-ttype=`.

### Target options

The any target in `-target="any target"` should specify either a group
of files (video, audio, subtitles, signs, fonts) or an absolute path to
a file or directory.

- `-target-priority=` sets the priority of options specified via
`-target=`.
  - `file_first` (default) - if options for a file are specified,
  options for the file's group and directory are ignored.
  - `dir_first` the reverse of **file_first**; if options for a
  directory are specified, file-specific options are ignored.
  - `mix` - mixed mode, where all options related to the file, group,
  and directory are considered.
- `-target="any target"` sets options for a specific file, a group of
files, or a directory. Supports:
  - [Flags](#flags)
  - Text options `-tlang=` and `-tname=`
  - Any options supported by **mkvmerge**. For these options, you need
  to follow the [syntax of mkvmerge options](
  https://mkvtoolnix.download/doc/mkvmerge.html).
- `-target="any target" -files` skips the files from target.
- `-target="any target" -specials=[--video-tracks, 0, --audio-tracks, 1]`
is a special option for recording unsupported arguments outside of
`-target`. Without explicitly specifying specials, you can simply write
`-target="any target" --video-tracks 0 --audio-tracks 1`.
- `-target=global` or `-target=` without any target returns the input
options to the global ones.



-----



# merge-tracks-with-video

## Cкрипт для быстрого объединения внешних дорожек с видео

## Как этим пользоваться

1. [Скачайте](
https://github.com/nujievik/merge-tracks-with-video/releases)
исполняемый файл (.exe) для Windows x64 или универсальный набор
скриптов (.pyz).
2. Если используете **набор скриптов**, установите [зависимости](
#%D0%B7%D0%B0%D0%B2%D0%B8%D1%81%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D0%B8).
3. Запустите в директории, содержащей видео или внешние дорожки.

Поведение по умолчанию можно изменить, настроив [файл конфигурации](
#%D1%84%D0%B0%D0%B9%D0%BB-%D0%BA%D0%BE%D0%BD%D1%84%D0%B8%D0%B3%D1%83%D1%80%D0%B0%D1%86%D0%B8%D0%B8)
или передав [аргументы командной строки](
#%D0%B0%D1%80%D0%B3%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B-%D0%BA%D0%BE%D0%BC%D0%B0%D0%BD%D0%B4%D0%BD%D0%BE%D0%B9-%D1%81%D1%82%D1%80%D0%BE%D0%BA%D0%B8).
В частности, можно не копировать скрипт в директорию с файлами, а
просто передать ее в качестве аргумента:

```
merge-tracks-with-video.exe "директория с файлами"
```

## Зависимости

- [Chardet](https://github.com/chardet/chardet)
- [MKVToolNix](https://mkvtoolnix.download/)
- [Python](https://www.python.org/downloads/)
- [FFprobe](https://ffmpeg.org/download.html) (для разделенного MKV)

## Лицензия

- **Собственный код**: [GNU General Public License v3.0](
https://www.gnu.org/licenses/gpl-3.0.html)
- **Chardet**: [GNU Lesser General Public License v2.1](
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **MKVToolNix**: [GNU General Public License v2.0](
https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
- **Python**: [PSF License](https://www.python.org/psf/license/)
- **FFprobe** (часть FFmpeg): [GNU Lesser General Public License v2.1](
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)

## Описание

Проект включает набор Python-скриптов, которые используют
пользовательские компоненты **Python**, **MKVToolNix** и **FFmpeg**.
Исходный код скриптов доступен в репозитории.

Для удобства использования в разделе [Releases](
https://github.com/nujievik/merge-tracks-with-video/releases) для
Windows x64 доступен скомпилированный исполняемый файл (.exe). А для
остальных систем - упакованный набор скриптов (.pyz).

Исполняемый файл для Windows содержит все необходимые для работы
компоненты:
- Набор скриптов из репозитория, скомпилированный с помощью
**PyInstaller**.
- Скомпилированные компоненты **MKVToolNix** (полученные с официального
[сайта MKVToolNix](https://mkvtoolnix.download/downloads.html#windows)).
- Скомпилированную версию **FFprobe** (полученную из релиза FFmpeg
win64-gpl от BtbN на [GitHub](
https://github.com/BtbN/FFmpeg-Builds/releases)).

Упакованный набор скриптов (.pyz) собран с помощью **zipapp** и требует
установки [зависимостей](
#%D0%B7%D0%B0%D0%B2%D0%B8%D1%81%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D0%B8).

## Функциональность

- Работает в Windows, GNU/Linux. Должен работать в macOS и BSD.
- Создает объединенный MKV контейнер без перекодирования дорожек.
- Находит файлы для объединения:
  - по частичному совпадению имени файла с именем видео
  - в родительских директориях стартовой директории
  - в поддиректориях директории видео
- Объединяет линкованное (mkv segment linking) видео.
- Позволяет обрезать часть MKV видео (для MKV с chapters).
- Ретаймит аудио и субтитры для объединенного линкованного или
обрезанного видео, чтобы не было рассинхрона.
- Выставляет кодировку для нераспознанных в UTF субтитров.
- Называет дорожки аудио и субтитров по хвосту их имени ИЛИ по имени
директории. (Исходное название, если оно есть, копируется без
изменений).
- Устанавливает язык дорожек аудио и субтитров по ключевым словам в
пути к файлам. (Исходный флаг языка также копируется без изменений).
- Устанавливает язык системной локали приоритетным для сортировки
дорожек и сортирует дорожки.
- Проставляет Forced, Default, Enabled флаги на основании сортировки
дорожек.
- Добавляет шрифты для субтитров в контейнер.
- Сортирует все шрифты по имени. (В том числе уже имевшиеся в
контейнере до объединения).
- Пропускает нераспознанные mkvmerge файлы и chapters.
- Поддерживает любые опции, поддерживаемые mkvmerge.
- Позволяет задать опции объединения для всех файлов в директории, для
групп файлов и для отдельных файлов.

## Режим по умолчанию

- Стартовая директория и директория сохранения - текущая рабочая
директория.
- Файлы для объединения ищутся в 3 родительских директориях и в
поддиректориях стартовой директории.
- Если старт в директории:
  - видео - все найденные дорожки ДОБАВЛЯЮТСЯ к исходным
  - внешних файлов - исходные дорожки ЗАМЕНЯЮТСЯ найденными
- Если старт в директории:
  - внешних аудио - ищется 1 штука внешних субтитров (приоритет поиск
  надписей)
  - внешних субтитров - оригинальное аудио сохраняется
- Сортируются дорожки в выходном файле в несколько уровней:
  - Видео > Аудио > Надписи > Субтитры
  - Forced (True > None > False, где True и False - заданные вручную
  значения, а None - не задано)
  - Default (True > None > False)
  - Enabled (True > None > False)
  - Локализованная дорожка > Неопределенные языки > Другие языки >
  Японская дорожка
  - Дорожка из файла с надписями > Дорожка из файла без надписей
- Проставляются Forced, Default, Enabled флаги:
  - Forced для всех отключено
  - Default включено для одной дорожки каждого типа (первой в
  сортировке). Если локализованная аудиодорожка установлена Default или
  Default установлена аудиорожка на языке субтитров, то Default для
  субтитров выключено
  - Enabled для всех включено
- Имя выходного файла ставится имя видео + суффикс что сделано
(_added_audio, _replaced_subs и т.п.)
- Линкованное видео разделяется на части, части записываются на диск и
потом объединяются.

## Работа с линкованным видео

По умолчанию линкованное видео записывается на диск сначала по частям,
потом из этих частей собирается целое видео. Фактически
перезаписывается в 2 раза больший объем диска, чем весит итоговое видео. 

Чтобы снизить трату дискового ресурса, можно отрезать прилинкованные
видео части (обычно это опенинг и эндинг). Тогда промежуточные части
записываться не будут, будет сразу писаться итоговое видео. Сделать это
можно с помощью флага:

```
python merge-tracks-with-video.pyz -linking
```

## Режим переназначения опций

Активируется передачей **аргументов командной строки** или настройкой
**файла конфигурации**. Непереданные опции остаются на дефолтных
значениях. Формируемая mkvmerge команда включает все неотключенные
вручную опции.

## Pro режим

Активируется установкой `pro` флага. Отключает сортировку шрифтов для
шрифтов в контейнере видео. Формирует чистую mkvmerge команду без опций
`mkvmerge -o outfile file1 file2 file3`. Можно комбинировать с режимом
переназначения, в частности включать в команду убранные опции.

## Файл конфигурации

- Должен располагаться в текущей рабочей директории.
- Имеет более низкий приоритет над **аргументами командной строки**.
(При указании значения опции в файле конфигурации и в аргументе
командной строки приоритет будет отдан последнему).
- Примеры синтаксиса и закомментированные значения опций перечислены в
[файле конфигурации](
https://github.com/nujievik/merge-tracks-with-video/blob/main/config-merge-tracks-with-video.ini).
- Чтобы изменить значение опции в **файле конфигурации**, нужно
раскомментировать строку и изменить значение справа.

## Аргументы командной строки

- Имеют приоритет над опциями в **файле конфигурации**. (При указании
значения опции в файле конфигурации и в аргументе командной строки
приоритет будет отдан последнему).
- Если аргумент не распознан, выполнение завершается.
- Аргументы можно передавать с разным синтаксисом.
  - допустимы префиксы `+`, `-`, `--`, `--no-`, `--save-` для
  поддерживаемых вне `-target=` аргументов. 
  - для неподдерживаемых вне `-target=` нужно соблюдать
  [синтаксис опций mkvmerge](
  https://mkvtoolnix.download/doc/mkvmerge.html).
  
## Список опций

### Версия

`-version` выводит текущую версию программы и завершает работу.

### Стартдир и Cейвдир

Можно указывать как абсолютные так и относительные текущей рабочей
директории пути. `стартдир` должен быть указан до `сейвдир`, если
`сейвдир` передается без ключа `-save-dir=`.

- `"стартовая директория"` или `-start-dir="стартовая директория"`
устанавливает стартовую директорию.
- `-save-dir="директория сохранения"` устанавливает директорию
сохранения. 

### Текстовые

Требуют указания текста после `=`. Например, `-tname="имя дорожки"`.

- `-locale` устанавливает приоритетный язык для сортировки дорожек.
- `-out-pname` и `-out-pname-tail` устанавливают начало и конец имени
выходных файлов соответственно. Между ними автоматически проставляется
номер файла, а в конце расширение .mkv.
- `-tlang` устанавливает язык дорожек.
- `-tname` устанавливает имя дорожек.

### Лимиты

Требуют указания целого неотрицательного числа после `=`. Например,
`-lim-gen=1`.

- `-lim-search-up` устанавливает количество родительских директорий в
которых ищутся видеофайлы для объединения (при запуске скрипта из
директории внешних файлов).
- `-lim-gen` устанавливает максимальное количество генерируемых видео.
- `-lim-forced-ttype` устанавливает максимальное количество
форсированных дорожек каждого типа (видео, аудио, надписи, субтитры).
По умолчанию 0. При увеличении нужно также включить флаг `forced`.
- `-lim-forced-signs` устанавливает лимит форсированных надписей. По
умолчанию 1. Для включения forced для надписей нужно также включить
флаг `+forced-signs`.
- `-lim-default-ttype` устанавливает лимит дефолтных дорожек каждого
типа. По умолчанию 1.
- `-lim-enabled-ttype` устанавливает лимит включенных дорожек каждого
типа. По умолчанию нет лимита, все дорожки включены.

### Диапазон генерации

Требует указания 1 или 2 целых неотрицательных чисел с разделителем.
В качестве разделителя можно использовать `-`, `,`, `:`. Например,
`-range-gen=2-8`.

- `-range-gen` устанавливает диапазон генерации для видеофайлов.
Берутся только видео, имеющие соответствующие внешние дорожки (если те
существуют). Видео берутся в алфавитном порядке.

### Удаление глав

`-rm-chapters=op,ed,prologue,preview` удаляет перечисленные через
запятую части видео (для MKV с chapters).

### Флаги

Флаги устанавливаются в True либо False через передачу соответствующих
значений. Например, `-subtitles=False`.
Для **аргументов командной строки** доступна установка через префиксы,
без прямой передачи значения. Префиксы `+` и `-` соответствуют True и
False. Например, `-subtitles`. Значение флага также отрицательно, если
аргумент передан с префиксом `--no-`. Но двойной дефис без `no` за ним
соответствует True. Например, `--subtitles` устанавливает True, а
`--no-subtitles` устанавливает False.

- `+pro` активирует Pro режим (дает чистую команду mkvmerge без флагов).
- `+verbose` активирует расширенный лог.

- `-search-dirs` отключает поиск файлов в директориях выше директории
старта. (Будет использоваться рекурсивный поиск в поддиректориях
старта).

- `-video` отключает копирование видеодорожек.
- `-audio` отключает добавление внешних аудиофайлов.
- `-orig-audio` отключает копирование аудиодорожек из видеофайла.
- `-target=" цель" -audio` отключает копирование аудиодорожек из
заданных файлов.
- `-subs` отключает добавление внешних субтитров.
- `-orig-subs` отключает копирование дорожек субтитров из видеофайла.
- `-target=" цель" -subs` отключает копирование дорожек субтитров из
заданных файлов.
- `-sub-charsets` отключает выставление кодировки для нераспознанных в
UTF субтитров.
- `-fonts` отключает добавление внешних шрифтов.
- `-orig-fonts` отключает копирование шрифтов из видеофайла.
- `-sort-orig-fonts` отключает сортировку уже имеющихся в
видеоконтейнере шрифтов в алфавитном порядке.

- `-chapters` отключает копирование глав.
- `-global-tags` отключает копирование глобальных тегов.

- `-linking` удаляет внешние части линкованного видео.
- `-opening` удаляет часть видео с опенингом (для MKV с chapters).
-  `-ending` удаляет часть видео с эндингом (для MKV с chapters).
- `-force-retiming` отключает ретайминг оригинальных аудио и субтитров
для линкованного видео, если основная часть видео не разделена.

- `-track-orders` отключает сортировку дорожек.

- `-tlangs` отключает добавление флагов языков.
- `-tnames` отключает добавление флагов имен дорожек.

- `-forceds` отключает добавление флагов Forced.
- `+forced` устанавливает положительное значение Forced. Для
конкретного файла если задан `-target=` или для всех если не задан.
Количество положительных значений ограничено лимитом
`-lim-forced-ttype=`, который по умолчанию 0.
- `+forced-signs` устанавливает положительное значение Forced для
надписей. Количество положительных значений ограничено
`-lim-forced-signs=`, по умолчанию 1.
- `-defaults` отключает добавление флагов Default.
- `+default` устанавливает положительное значение Default. Количество
положительных значений ограничено `-lim-default-ttype=`, по умолчанию 1.
- `-enableds` отключает добавление флагов Enabled.
- `-enabled` устанавливает отрицательное значение Enabled. По умолчанию
всем дорожкам проставляется положительное Enabled, а количество
`-lim-enabled-ttype=` не ограничено.

### Target опции

В качестве цели в `-target=" цель"` нужно указывать группу файлов
(video, audio, subtitles, signs, fonts) или абсолютный путь к файлу или
директории файла.

- `-target-priority=` устанавливает приоритет опций заданных через
`-target=`. 
  - `file_first` установлен по умолчанию - если заданы опции для файла,
  то опции для группы и директории этого файла не учитываются. 
  - `dir_first` зеркальное отражение, если задано для директории, для
  файла не учитываются. 
  - `mix` смешанный режим учитывает все опции, относящиеся к файлу,
  группе и директории файла.
- `-target=" цель"` устанавливает опции для конкретного файла, группы
файлов (video, audio, signs, subtitles) или для директории.
Поддерживает: 
  - [Флаги](#%D1%84%D0%BB%D0%B0%D0%B3%D0%B8)
  - текстовые `-tlang` и `-tname`
  - любые опции, поддерживаемые mkvmerge. Для опций mkvmerge нужно
  соблюдать [синтаксис опций mkvmerge](
  https://mkvtoolnix.download/doc/mkvmerge.html). 
- `-target=" цель" -files` пропускает заданные файлы.
- `-target=" цель" -specials=[--video-tracks, 0, --audio-tracks, 1]`
специальная опция для записи неподдерживаемых вне `-target` опций.
Без явного указания specials можно просто писать
`-target=" цель" --video-tracks 0 --audio-tracks 1"`
- `-target=global` или `-target=` без указания пути или группы
возвращает ввод опций к глобальным.
