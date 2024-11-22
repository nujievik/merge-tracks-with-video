# generate-video-with-these-files

## Cкрипт для добавления внешних дорожек в видео, объединения и ретайминга дорожек линкованного .mkv видео.

## Лицензия

- Собственный код: GNU General Public License v3.0
- MKVToolNix: GNU General Public License v2.0
- Python: PSF License

## Описание

Этот проект включает Python-скрипт, который использует компоненты **MKVToolNix** и **Python**. Исходный код доступен в репозитории.

Для удобства использования, в разделе [Releases](https://github.com/nujievik/generate-video-with-these-files-script/releases) доступен скомпилированный исполняемый файл, который включает:

- generate-video-with-these-files.py скрипт, скомпилированный с помощью **PyInstaller**.
- Встроенную скомпилированную версию **Python**, необходимую для работы скрипта.
- Встроенные скомпилированные компоненты **MKVToolNix**.

Все компоненты (скрипт, Python и MKVToolNix) включены в один исполняемый файл. Это позволяет вам использовать проект без необходимости устанавливать Python или MKVToolNix.

## Зависимости

- **MKVToolNix**: Включено в исполняемый файл, лицензировано под [GNU GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html).
- **Python**: Включено в исполняемый файл, лицензировано под [PSF License](https://www.python.org/psf/license/).


## Функциональность

- Работает в Windows, GNU/Linux. Должен работать в macOS и BSD.
- Создает объединенный MKV контейнер без перекодирования дорожек.
- Находит файлы для объединения по частичному совпадению имени файла с именем видео.
- Находит файлы в поддиректориях директории видео.
- Объединяет линкованное (mkv segment linking) видео.
- Ретаймит аудио и субтитры для объединенного линкованного видео, чтобы не было рассинхрона.
- Называет дорожки аудио и субтитров по хвосту их имени ИЛИ по имени директории. Исходное название, если оно есть, копируется без изменений.
- Добавляет шрифты для субтитров в контейнер.
- Ставит кодировку cp1251 для нераспознанных в UTF-8 субтитров.
- Удаляет нераспознанные chapters, которые вызывают ошибку генерации.
- Позволяет значительно изменить поведение по умолчанию, добавив аргументы вызова.
- Поддерживает любые аргументы, поддерживаемые mkvmerge.
- Позволяет задать аргументы объединения для всех файлов в директории, для групп файлов (видео, аудио, субтитры) и для отдельных файлов.


## Как этим пользоваться

1. Скачать архив, распаковать.
2. Закинуть исполняемый файл в папку с видео, внешними аудио или внешними субтитрами.
3. Запустить.

Можно не копировать в директорию с файлами, а просто передать ее в качестве аргумента:
`generate-video-with-these-files.exe "директория с файлами"`

Поведение скрипта зависит от стартовой директории и переданных аргументов (опционально).


## Режим по умолчанию

- Стартовая директория и директория сохранения = текущая рабочая директория.
- Если старт в директории видео, все найденные дорожки будут ДОБАВЛЕНЫ к исходным.
- Если старт в директории внешних файлов, исходные дорожки будут ЗАМЕНЕНЫ найденными.
- Если старт в директории внешних аудио, ищутся внешние субтитры (приоритет поиск надписей).
- Если старт в директории внешних субтитров, оригинальное аудио сохраняется.


## Аргументы вызова (опционально):

- Символом `|` в списке ниже отделены разные синтаксисы одного и того же аргумента.
- Можно передать любое количество аргументов.
- Можно передавать аргументы в любом порядке, но `стартдир` должен быть указан до `сейвдир`, если `сейвдир` передается без ключа `--save-dir=`
- Непереданные аргументы остаются на дефолтных значениях.
- Если аргумент не распознан, выполнение завершается.
- `стартдир` и `сейвдир` аргументы - пути к соответствующим директориям. Можно указывать как абсолютный так и относительный путь (относительно текущей рабочей директории).
- `--output-partname=` устанавливает начало имени выходных файлов. В конце автоматически добавляется номер файла. `--output-partname-tale=` устанавливает конец имени выходных файлов после номера файла (без расширения). В конце автоматически добавляется расширение `.mkv`
- `--limit` аргументы требуют дописать число после `=`.
- `--range-generate=` устанавливает диапазон генерации для видеофайлов. Берутся только видео, имеющие соответствующие внешние аудио-сабы (если те существуют). Если в одной директории с сериями файлы OP, ED без соответствующих внешних файлов, они не учитываются в диапазоне. Видео берутся в алфавитном порядке. Нумерация в диапазоне начинается с 1.
- `--save-` аргументы сохраняют, а `--no-` аргументы удаляют соответствующие параметры (по умолчанию все максимально сохраняется).
- `-original-` аргументы относятся к дорожкам видеофайла.
- Те же аргументы без -original- относятся к внешним файлам.
- `-fonts` и `-attachments` аргументы эквиваленты.
- `--no-add-tracknames` отключает добавление имен дорожек из хвоста имени файла или имени директории. Но если имя задано через `--for=path --trackname="имя дорожки"`, то имя дорожки все равно будет добавлено.

- `--for-priority=` устанавливает приоритет аргументов из `--for=`.
По умолчанию `--for-priority=file_first` приоритет файл>группа файла>директория файла. Если заданы `--for=` для файла, то аргументы заданные для группы этого файла и для директории файла будут игнорироваться. Если заданы для группы, то для директории будут игнорироваться.
`--for-priority=dir_first` зеркальное отражение. Приоритет директория файла>группа файла>файл.
`--for-priority=mix` объединяет аргументы из всех --for=, относящихся к файлу.

- `--for=` устанавливает аргументы для группы файлов или для директории файлов или для файла.
- Аргумент `--for="путь или группа" --no-files` пропускает файлы для соответствующей группы или пути.
- Аргумент `--for="путь или группа" --trackname="имя трека"` устанавливает имя дорожки без необходимости указывать ее номер, что требуется в оригинальном синтаксисе `mkvmerge`.
- Все остальные аргументы после `--for="путь или группа"` передадутся в команду `mkvmerge` в том виде, в котором их ввели. Нужно соблюдать [синтаксис команд mkvmerge](https://mkvtoolnix.download/doc/mkvmerge.html).

- `--for=all` или `--for=` без указания пути или группы возвращает ввод аргументов к общим.

## Полный список аргументов и примеры синтаксиса:

```
стартдир | 'стартовая директория с пробелом' | --start-dir=стартдир | --start-dir="стартдир с пробелом в пути"
сейвдир | --save-dir='директория сохранения с пробелом'
--output-partname=началоимени | --output-partname="начало имени выходных файлов с пробелом. В конце автоматически добавляется номер файла"
--output-partname-tale=конецимени | --output-partname-tale='конец имени с пробелом. Перед ним идет номер файла. После - расширение .mkv'
--limit-search-up=3
--limit-generate=99999
--range-generate=1-8 | --range-generate=2:9 | --range-generate=3,6 | --range-generate=11 | --range-generate=:4
--extended-log
--no-extended-log
--pro-mode
--no-pro-mode
--save-global-tags
--no-global-tags
--save-chapters
--no-chapters
--save-audio
--no-audio
--save-original-audio
--no-original-audio
--save-subtitles
--no-subtitles
--save-original-subtitles
--no-original-subtitles
--save-fonts | --save-attachments
--no-fonts | --no-attachments
--save-original-fonts | --save-original-attachments
--no-original-fonts | --no-original-attachments
--sort-original-fonts | --sort-original-attachments
--no-sort-original-fonts | --no-sort-original-attachments
--add-tracknames
--no-add-tracknames
--for-priority=file_first
--for-priority=dir_first
--for-priority=mix
--for=группафайловилипуть | --for="группа файлов или путь с пробелом. Устанавливает следующие за этим аргументы для указанного пути или группы."
--for=путь --save-files
--for="путь или группа" --no-files
--for="путь или группа" --trackname="имя дорожки"
--for="путь или группа" любые аргументы поддерживаемые mkvmerge. В каком виде написаны в таком виде и подставятся в команду mkvmerge
```


## Примеры изменения поведения по умолчанию

Все примеры написаны для python скрипта. Если вы запускаете `.exe` просто замените `python generate-video-with-these-files.py` на `generate-video-with-these-files.exe`

### Изменить директорию старта
`python generate-video-with-these-files.py --start-dir="путь к директории"`

### Изменить директорию сохранения
`python generate-video-with-these-files.py --save-dir="путь к директории"`

### Изменить имя выходных файлов
Установить начало имени. В конце будет добавлен номер файла и расширение .mkv.:
```
python generate-video-with-these-files.py --output-partname="prefix "
```
Установить хвост имени после номера файла. В конце автоматически добавится .mkv:
```
python generate-video-with-these-files.py --output-partname-tale=" suffix"
```

#### Пример установить имя 'Death Note - номерсерии (BDRip 1920x1080 x264 VFR 10bit FLAC).mkv'
`python generate-video-with-these-files.py --output-partname="Death Note - " --output-partname-tale=" (BDRip 1920x1080 x264 VFR 10bit FLAC)"`

### Добавить только внешние аудио / субтитры / шрифты
Аудио:
```
python generate-video-with-these-files.py --save-audio --no-subtitles --no-fonts
```
Субтитры:
```
python generate-video-with-these-files.py --save-subtitles --no-audio --no-fonts
```
Шрифты:
```
python generate-video-with-these-files.py --save-fonts --no-audio --no-subtitles
```

### Добавить дорожки к оригинальным, а не заменить оригинальные
`python generate-video-with-these-files.py --save-original-audio --save-original-subtitles`

### Заменить оригинальные дорожки внешними, а не добавить
`python generate-video-with-these-files.py --no-original-audio --no-original-subtitles --no-original-fonts`

### Удалить все дорожки аудио / субтитров / все шрифты
Аудио:
```
python generate-video-with-these-files.py --no-audio --no-original-audio
```
Субтитры:
```
python generate-video-with-these-files.py --no-subtitles --no-original-subtitles
```
Шрифты:
```
python generate-video-with-these-files.py --no-fonts --no-original-fonts
```

### Обработать только часть файлов
Через диапазон генерации.
В этом случае создаются файлы только для указанного диапазона.
```
python generate-video-with-these-files.py --range-generate=8-10
```

Через лимит генерации.
В этом случае создастся заданное количество файлов. Файлы перебираются с начала. Если выходной файл существует, счетчик генерации не увеличивается, берется следующий файл.
```
python generate-video-with-these-files.py --limit-generate=4
```

### Удалить главы и теги из видео
`python generate-video-with-these-files.py --no-chapters --no-global-tags`

### Не называть дорожки именами из хвоста имени или директории
`python generate-video-with-these-files.py --no-add-tracknames`

### Не сортировать уже имеющиеся шрифты в алфавитном порядке
`python generate-video-with-these-files.py --no-sort-original-fonts`

### Получить чистую команду 'mkvmerge -o outfile file1 file2 file3' чтобы добавить любые аргументы через --for
`python generate-video-with-these-files.py --no-add-tracknames --no-sort-original-fonts`

### Не добавлять файлы из определенной директории
`python generate-video-with-these-files.py --for="путь к директории" --no-files`

### Задать имя дорожки для файлов из директории или для конкретного файла
`python generate-video-with-these-files.py --for="путь к директории или файлу" --trackname="имя дорожки"`


---


# generate-video-with-these-files

## The script for adding external tracks to a video, merging, and retiming tracks of .mkv segment linking video.

## License

- Custom Code: GNU General Public License v3.0
- MKVToolNix: GNU General Public License v2.0
- Python: PSF License

## Description

This project includes a Python script that uses components **MKVToolNix** and **Python**. The source code is available in the repository.

For convenience, a compiled executable file is available in the [Releases](https://github.com/nujievik/generate-video-with-these-files-script/releases) section, which includes:

- The `generate-video-with-these-files.py` script, compiled using **PyInstaller**.
- A built-in compiled version of **Python** required to run the script.
- Built-in compiled components of **MKVToolNix**.

All components (script, Python, and MKVToolNix) are bundled into a single executable file. This allows you to use the project without needing to install Python or MKVToolNix.

## Dependencies

- **MKVToolNix**: Included in the executable files, licensed under [GNU GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html).
- **Python**: Included in the executable file, licensed under the [PSF License](https://www.python.org/psf/license/).

## Functionality

- Works on Windows, GNU/Linux. It should also work on macOS and BSD.
- Creates a merged MKV container without re-encoding the tracks.
- Finds files for merging based on partial filename matching with the video name.
- Searches for files in subdirectories of the video directory.
- Merges linked (mkv segment linking) videos.
- Re-timings audio and subtitles for the merged linked video to avoid synchronization issues.
- Names audio and subtitle tracks based on the tail of their filenames OR the directory name. If there is an original name, it is copied without changes.
- Adds subtitle fonts to the container.
- Sets cp1251 encoding for subtitles that are not recognized in UTF-8.
- Removes unrecognized chapters that cause generation errors.
- Allows significant changes to the default behavior by adding call arguments.
- Supports any arguments supported by mkvmerge.
- Allows specifying merge arguments for all files in a directory, groups of files (video, audio, subtitles), and individual files.

## How to Use

1. Download and extract the archive.
2. Place the executable file in the folder with the video, external audio, or external subtitles.
3. Run it.

You don't have to copy it to the folder with files; you can just pass the directory as an argument:
`generate-video-with-these-files.exe "directory with files"`

The script's behavior depends on the starting directory and the passed arguments (optional).

## Default Mode

- Starting directory and save directory = current working directory.
- If started in the video directory, all found tracks will be ADDED to the original ones.
- If started in the external files directory, the original tracks will be REPLACED by the found ones.
- If started in the external audio directory, it searches for external subtitles (with a preference for text subtitle search).
- If started in the external subtitle directory, the original audio is kept.

## Call Arguments (Optional):

- Different syntaxes of the same argument are separated by `|` in the list below.
- Any number of arguments can be passed.
- Arguments can be passed in any order, but the `startdir` must be specified before `savedir` if `savedir` is passed without the `--save-dir=` key.
- Unpassed arguments remain at their default values.
- If an argument is unrecognized, the execution will stop.
- `startdir` and `savedir` arguments are paths to the corresponding directories. You can specify both absolute and relative paths (relative to the current working directory).
- `--output-partname=` sets the beginning of the output filenames. A file number is automatically added at the end. `--output-partname-tale=` sets the end of the output filenames after the file number (without extension). The `.mkv` extension is automatically added.
- `--limit` arguments require a number after `=`.
- `--range-generate=` sets the generation range for video files. Only videos with corresponding external audio and subtitles (if they exist) are taken. If OP, ED files are in the same directory as episodes without corresponding external files, they will not be included in the range. Videos are taken in alphabetical order. The range numbering starts at 1.
- `--save-` arguments save, while `--no-` arguments remove corresponding parameters (by default, everything is saved).
- `-original-` arguments refer to video track files.
- The same arguments without -original- refer to external files.
- `-fonts` and `-attachments` arguments are equivalent.
- `--no-add-tracknames` disables adding track names from the tail of the file name or directory name. However, if a name is specified via `--for=path --trackname="track name"`, the track name will still be added.

- `--for-priority=` sets the priority of arguments from `--for=`.
By default, `--for-priority=file_first` prioritizes file > file group > file directory. If `--for=` is specified for a file, arguments for the file group and directory will be ignored. If specified for a group, the directory arguments will be ignored.
`--for-priority=dir_first` reverses the order. The priority is directory > file group > file.
`--for-priority=mix` merges arguments from all `--for=` related to the file.

- `--for=` sets arguments for a file group, file directory, or individual file.
- The argument `--for="path or group" --no-files` skips files for the specified group or path.
- The argument `--for="path or group" --trackname="track name"` sets the track name without needing to specify the track number, which is required in the original `mkvmerge` syntax.
- All other arguments after `--for="path or group"` will be passed directly to the `mkvmerge` command as entered. Be sure to follow the [mkvmerge command syntax](https://mkvtoolnix.download/doc/mkvmerge.html).

- `--for=all` or `--for=` without specifying a path or group applies arguments globally.

## Full List of Arguments and Syntax Examples:

```
startdir | 'starting directory with spaces' | --start-dir=startdir | --start-dir="startdir with spaces"
savedir | --save-dir='save directory with spaces'
--output-partname=filenameprefix | --output-partname="output filename prefix with spaces. A file number is automatically added at the end"
--output-partname-tale=filenamepostfix | --output-partname-tale='filename suffix with spaces. The file number is added before it. Extension .mkv follows'
--limit-search-up=3
--limit-generate=99999
--range-generate=1-8 | --range-generate=2:9 | --range-generate=3,6 | --range-generate=11 | --range-generate=:4
--extended-log
--no-extended-log
--pro-mode
--no-pro-mode
--save-global-tags
--no-global-tags
--save-chapters
--no-chapters
--save-audio
--no-audio
--save-original-audio
--no-original-audio
--save-subtitles
--no-subtitles
--save-original-subtitles
--no-original-subtitles
--save-fonts | --save-attachments
--no-fonts | --no-attachments
--save-original-fonts | --save-original-attachments
--no-original-fonts | --no-original-attachments
--sort-original-fonts | --sort-original-attachments
--no-sort-original-fonts | --no-sort-original-attachments
--add-tracknames
--no-add-tracknames
--for-priority=file_first
--for-priority=dir_first
--for-priority=mix
--for=filegrouporpath | --for="filepath or file directory with spaces. Sets following arguments for the specified path or group."
--for=path --save-files
--for="path or group" --no-files
--for="path or group" --trackname="track name"
--for="path or group" any arguments supported by mkvmerge. They will be passed to the mkvmerge command as is.
```


## Examples of Changing Default Behavior

All examples are written for the Python script. If you're using the `.exe`, simply replace `python generate-video-with-these-files.py` with `generate-video-with-these-files.exe`

### Change the Start Directory
`python generate-video-with-these-files.py --start-dir="path to the directory"`

### Change the Save Directory
`python generate-video-with-these-files.py --save-dir="path to the directory"`

### Change the Output Filenames
Set the prefix of the name. A file number and the .mkv extension will be added at the end:
```
python generate-video-with-these-files.py --output-partname="prefix "
```
Set the suffix of the name after the file number. The .mkv extension will be automatically added at the end:
```
python generate-video-with-these-files.py --output-partname-tale=" suffix"
```

#### Example to set the name 'Death Note - episodeNumber (BDRip 1920x1080 x264 VFR 10bit FLAC).mkv'
`python generate-video-with-these-files.py --output-partname="Death Note - " --output-partname-tale=" (BDRip 1920x1080 x264 VFR 10bit FLAC)"`

### Add Only External Audio / Subtitles / Fonts
Audio:
```
python generate-video-with-these-files.py --save-audio --no-subtitles --no-fonts
```
Subtitles:
```
python generate-video-with-these-files.py --save-subtitles --no-audio --no-fonts
```
Fonts:
```
python generate-video-with-these-files.py --save-fonts --no-audio --no-subtitles
```

### Add Tracks to Originals Instead of Replacing Originals
`python generate-video-with-these-files.py --save-original-audio --save-original-subtitles`

### Replace Original Tracks with External Ones Instead of Adding
`python generate-video-with-these-files.py --no-original-audio --no-original-subtitles --no-original-fonts`

### Remove All Audio / Subtitle Tracks / Fonts
Audio:
```
python generate-video-with-these-files.py --no-audio --no-original-audio
```
Subtitles:
```
python generate-video-with-these-files.py --no-subtitles --no-original-subtitles
```
Fonts:
```
python generate-video-with-these-files.py --no-fonts --no-original-fonts
```

### Process Only Part of the Files
Through the generation range.
In this case, files will be created only for the specified range.
```
python generate-video-with-these-files.py --range-generate=8-10
```

Through the generation limit.
This will create the specified number of files. Files are iterated from the start. If an output file exists, the generation counter does not increase, and the next file is used.
```
python generate-video-with-these-files.py --limit-generate=4
```

### Remove Chapters and Tags from the Video
`python generate-video-with-these-files.py --no-chapters --no-global-tags`

### Do Not Name Tracks Based on the Tail of the Filename or Directory
`python generate-video-with-these-files.py --no-add-tracknames`

### Do Not Sort Existing Fonts Alphabetically
`python generate-video-with-these-files.py --no-sort-original-fonts`

### Get a Clean `mkvmerge` Command 'mkvmerge -o outfile file1 file2 file3' to Add Any Arguments Through `--for`
`python generate-video-with-these-files.py --no-add-tracknames --no-sort-original-fonts`

### Do Not Add Files from a Specific Directory
`python generate-video-with-these-files.py --for="path to directory" --no-files`

### Set Track Name for Files from a Directory or a Specific File
`python generate-video-with-these-files.py --for="path to directory or file" --trackname="track name"`

