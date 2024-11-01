Кроссплатформенный скрипт для добавления/замены дорожек в видео. / Cross-platform script for adding/replacing tracks in video.

Возможности:
- Работает в Windows, Wine и GNU/Linux. Должен работать в macOS и BSD.
- Создает объединенный MKV контейнер без перекодирования дорожек.
- Ищет файлы для объединения по частичному совпадению имени файла с именем видео.
- Объединяет линкованное видео.
- Ретаймит аудио и субтитры для объединенного линкованного видео, чтобы не было рассинхрона.
- Называет дорожки аудио и субтитров по хвосту их имени ИЛИ по имени директории. Исходное название, если оно есть, копируется без изменений.
- Добавляет шрифты для субтитров.
- Ставит кодировку cp1251 для нераспознанных в UTF-8 субтитров.
- Удаляет нераспознанные chapters, которые вызывают ошибку генерации.

Требования:
- Python 3.4+, прописанный в Path (по умолчанию прописывается при установке)
- MKVToolNix. Или прописанный в Path или установленный в директорию по умолчанию (для Windows)

Как этим пользоваться:
1. Иметь установленные Python и MKVToolNix (см. Требования)
2. Запустить скрипт в папке с видео, внешними аудио или внешними субтитрами.
   - В Windows можно просто запустить батник.
   - В других системах через терминал:
     `python generate-video-with-these-files.py`
   - Можно запустить из любого места, передав стартовую директорию в качестве аргумента:
     `python generate-video-with-these-files.py "стартовая-директория"`

Поведение скрипта зависит от стартовой директории и переданных аргументов (опционально).
Режим по умолчанию:
- Если аргументов не передано, то стартовая директория и директория сохранения = директории скрипта.
- Если старт в директории видео, все найденные дорожки будут ДОБАВЛЕНЫ к исходным.
- Если старт в директории внешних файлов, исходные дорожки будут ЗАМЕНЕНЫ найденными.
- Если старт в директории внешних аудио, ищутся внешние субтитры (приоритет поиск надписей).
- Если старт в директории внешних субтитров, оригинальное аудио сохраняется.

Аргументы вызова (опционально):
- Можно передать любое количество аргументов.
- Можно передавать аргументы в любом порядке, но `start-dir` должен быть указан до `save-dir`.
- Непереданные аргументы остаются на дефолтных значениях.
- Нераспознанные аргументы пропускаются.
- `start-dir` и `save-dir` аргументы - пути к соответствующим директориям. Можно указывать как абсолютный так и относительный путь (относительно python скрипта).
- `--limit` аргументы требуют дописать число после `=`.
- `--save-` аргументы сохраняют, а `--no-` аргументы удаляют соответствующие параметры (по умолчанию все максимально сохраняется).
- `-original-` аргументы относятся к дорожкам видеофайла.
- Те же аргументы без `-original-` относятся к внешним файлам.
- `-fonts` и `-attachments` аргументы эквиваленты.

Полный список аргументов:
```
start-dir
save-dir
--limit-search-up=X
--limit-generate=Y
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
--save-fonts
--no-fonts
--save-original-fonts
--no-original-fonts
--save-attachments
--no-attachments
--save-original-attachments
--no-original-attachments
```

---

Cross-platform script for adding/replacing tracks in video.

Features:
- Works on Windows, Wine, GNU/Linux, macOS, and BSD.
- Creates a merged MKV container without re-encoding tracks.
- Searches for files to merge by partial filename match with the video name.
- Merges linked/segment linking video .
- Retimes audio and subtitles for the merged linked video to avoid synchronization issues.
- Names audio and subtitle tracks by the tail of their names OR by the directory name. The original name, if available, is copied unchanged.
- Adds fonts for subtitles.
- Sets cp1251 encoding for subtitles not recognized in UTF-8.
- Removes unrecognized chapters that cause generation errors.

Requirements:
- Python 3.4+ installed and added to PATH (usually done automatically during installation).
- MKVToolNix. Either added to PATH or installed in the default directory (for Windows).

How to Use:
1. Ensure Python and MKVToolNix are installed (see Requirements).
2. Run the script in a folder containing video, external audio, or external subtitles.
   - In Windows, you can simply run the batch file.
   - In other systems via terminal: `python generate-video-with-these-files.py`
   - You can run it from any location by passing the starting directory as an argument: `python generate-video-with-these-files.py "start-directory"`

Script Behavior: The behavior of the script depends on the starting directory and any passed arguments (optional).

Default Mode:
- If no arguments are passed, the starting directory and save directory are set to the script’s directory.
- If starting in the video directory, all found tracks will be ADDED to the original.
- If starting in the external files directory, the original tracks will be REPLACED with the found ones.
- If starting in the external audio directory, external subtitles will be searched for (priority is given to subtitle search).
- If starting in the external subtitles directory, the original audio is preserved.

Arguments (Optional):
- You can pass any number of arguments.
- Arguments can be passed in any order, but `start-dir` must be specified before `save-dir`.
- Unrecognized arguments are ignored.
- `start-dir` and `save-dir` arguments are paths to the corresponding directories. You can specify both absolute and relative paths (relative to the Python script).
- `--limit` arguments require a number to be added after the `=`.
- `--save-` arguments preserve the corresponding parameters, while `--no-` arguments remove them (by default, everything is preserved).
- `-original-` arguments refer to the tracks of the video file.
- The same arguments without `-original-` refer to external files.
- `-fonts` and `-attachments` arguments are equivalent.

Complete List of Arguments:
```
start-dir
save-dir
--limit-search-up=X
--limit-generate=Y
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
--save-fonts
--no-fonts
--save-original-fonts
--no-original-fonts
--save-attachments
--no-attachments
--save-original-attachments
--no-original-attachments
```
