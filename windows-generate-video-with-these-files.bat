@echo off
::windows-generate-video-with-these-files-v0.3.2
::This program is part of the generate-video-with-these-files-script repository
::Licensed under GPL-3.0. See LICENSE file for details.
::Author: nujievik Email: nujievik@gmail.com

setlocal enabledelayedexpansion
::задаем константы и инициализируем переменные
call :set_constants_and_init_variables

:: запрашиваем лимит файлов
call :ask_file_limit
:: спрашиваем добавлять ли сабы
call :ask_about_add_subtitle

:: ищем видеодиректорию через аудио
call :search_video_dir_from_audio

:: если видеодир не найдена ищем директорию через сабы
if !video_dir_found! equ 0 (
    call :search_video_dir_from_subtitle
)

:: если сабдир не найдена и поиск не выполнен
if !subtitle_dir_found_or_search_completed! equ 0 (
    call :search_subtitle_dir
)

:: если сабдир найдена ищем директорию шрифтов
if !subtitle_dir_found! equ 1 (
    call :search_font_dir
)

:: если фонтдир найдена ищем-качаем mkvtool иначе ffmpeg
if !font_dir_found! equ 1 (
    call :search_mkvtoolnix
    ::создаем фонлист
    call :create_font_attach_list

) else (
    call :search_and_download_ffmpeg_ffprobe
)

:: выполняем генерацию найденных видео с аудио-сабами
call :execute_generate

:: успешное завершение
call :success



:set_constants_and_init_variables
:: расширения для аудио и видео файлов
set "AUDIO_EXTENSIONS=mka m4a aac ac3 dts dtshd eac3 ec3 flac mp2 mpa mp3 opus truehd wav 3gp flv m2ts mkv mp4 mpeg mpg mov ts ogg ogm webm"
set "VIDEO_EXTENSIONS=mkv m4v mp4 avi h264 hevc ts 3gp flv m2ts mpeg mpg mov ogm webm"
:: Расширения требующие дополнительной проверки - контейнеры, которые могут содержать как видео так и аудио
set "MIX_EXTENSIONS=mkv mp4 avi 3gp flv m2ts mpeg mpg mov ogg ogm ts webm wmv"
:: Расширения субтитров
set "SUBTITLE_EXTENSIONS=ass mks ssa sub srt ttml dxf"
::расширения шрифтов
set "FONT_EXTENSIONS=ttf otf"

:: Слова, по которым ищется директория субтитров, если не найдены сабы рядом с аудио или видео - нечувствительно к регистру т.е. SUB эквивалентно sub или Sub
set "SEARCH_STRING_SUB=sign Sub"
:: Слова, по которым ищется фонтдир если шрифты не найдены в сабдир - нечувствительно к регистру
set "SEARCH_STRING_FONT=Font"


:: Параметры обработки ffmpeg
set "FFMPEG_PARAMS_AUDIO_ONLY=-c:v copy -c:a copy -map 0:v -map 1:a -disposition:v:0 default -disposition:a:0 default"
set "FFMPEG_PARAMS_SUB_ONLY=-c:v copy -c:s copy -map 0 -map 1:s -disposition:v:0 default -disposition:a:0 default -disposition:s:0 default"
set "FFMPEG_PARAMS_AUDIO_SUB=-c:v copy -c:a copy -c:s copy -map 0:v -map 1:a -map 2:s -disposition:v:0 default -disposition:a:0 default -disposition:s:0 default"
:: параметры проверки через ffprobe на наличие видеодорожки
set "FFPROBE_PARAMS=-v error -select_streams v:0 -show_entries stream=codec_type -of default=noprint_wrappers=1:nokey=1"

:: путь к директории ffmpeg
set "FFMPEG_DIR=%USERPROFILE%\Downloads\ffmpeg-master-latest-win64-gpl\bin"
:: откуда и куда скачивается и распаковывается ffmpeg
set "FFMPEG_SOURCE_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
set "FFMPEG_SOURCE_ZIP=%USERPROFILE%\Downloads\ffmpeg-master-latest-win64-gpl.zip"
set "FFMPEG_EXTRACT_DIR=%USERPROFILE%\Downloads"
set "FFMPEG_EXE=%FFMPEG_DIR%\ffmpeg.exe"
set "FFPROBE_EXE=%FFMPEG_DIR%\ffprobe.exe"

set "MKVTOOLNIX_DIR=%USERPROFILE%\Downloads\mkvtoolnix"
:: откуда и куда скачивается и распаковывается mkvtoolnix
set "MKVTOOLNIX_SOURCE_URL=https://mkvtoolnix.download/windows/releases/87.0/mkvtoolnix-64-bit-87.0.7z"
set "MKVTOOLNIX_SOURCE_7Z=mkvtoolnix-64-bit-87.0.7z"
set "MKVTOOLNIX_EXTRACT_DIR=%USERPROFILE%\Downloads"
set "MKVMERGE_EXE=%MKVTOOLNIX_DIR%\mkvmerge.exe"
set "MKVINFO_EXE=%MKVTOOLNIX_DIR%\mkvinfo.exe"
set "MKVEXTRACT_EXE=%MKVTOOLNIX_DIR%\mkvextract.exe"


:: определяем директорию скрипта
set "SCRIPT_DIR=%~dp0"
:: Удалить завершающий слэш в пути
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"


:: сколько директорий над директорией скрипта проверяется на наличие видео
set "SEARCH_LIMIT=3"


set "audio_dir_found=0"
set "video_dir_found=0"
set "subtitle_dir_found=0"
set "font_dir_found=0"
set /a count_search_video_dir=0
set /a count_generated_file=0
set "subtitle_found=0"
set "compliance_extension=0"
set "start_search_video_dir_from_subtitle=0"
set "start_search_font_dir=0"
set "font_attach_list_created=0"
set "file_with_search_ext_found=0"

goto :EOF



:ask_file_limit
:: Запрашиваем у пользователя количество обрабатываемых файлов
echo Enter the limit number of files to generate. [Press Enter to generate for all files]:
set /p "FILE_LIMIT=> "

:: Устанавливаем значение по умолчанию для FILE_LIMIT, если ввод пустой или некорректный
if not defined FILE_LIMIT (
    set FILE_LIMIT=999999
) else (
    for /f "delims=0123456789" %%i in ("%FILE_LIMIT%") do (
        echo Invalid input. Start generate for all files.
        set FILE_LIMIT=999999
    )
)
goto :EOF



:ask_about_add_subtitle
echo Do you want to search and adding subtitle? [y/N] or [Press Enter to adding subtitle]:
set /p "user_input=> "

:: обработка ввода пользователя
if /i "!user_input!" equ "no" (
    call :set_flag_to_not_add_subtitle
    goto :EOF
)
if /i "!user_input!" equ "n" (
    call :set_flag_to_not_add_subtitle
    goto :EOF
)

if /i "!user_input!" equ "yes" (
    call :set_flag_to_add_subtitle
    goto :EOF
)
if /i "!user_input!" equ "y" (
    call :set_flag_to_add_subtitle
    goto :EOF
)

echo Input is not correct.
call :set_flag_to_add_subtitle
goto :EOF


:set_flag_to_not_add_subtitle
echo Subtitle will NOT be search and adding.
set "adding_subtitle=0"
set "subtitle_dir_found_or_search_completed=1"
set "subtitle_dir_found=0"
goto :EOF

:set_flag_to_add_subtitle
echo Subtitle will be search and adding.
set "adding_subtitle=1"
set "subtitle_dir_found_or_search_completed=0"
goto :EOF



:search_video_dir_from_audio
set "count_search_video_dir=0"
:: переходим в директорию скрипта
cd /d "%SCRIPT_DIR%"
set "search_extensions=%AUDIO_EXTENSIONS%"
set "search_dir=%SCRIPT_DIR%"
call :search_video_dir

::если сабы не добавляем и видеодир не найден
if !adding_subtitle! equ 0 (
    if !video_dir_found! equ 0 (
        echo Error. Video directory not found. Was checked "%SCRIPT_DIR%" and !count_search_video_dir! directories upper. Exit...
        pause
        exit
    )
)
goto :EOF


:search_video_dir_from_subtitle
set "start_search_video_dir_from_subtitle=1"
set "count_search_video_dir=0"
:: переходим в директорию скрипта
cd /d "%SCRIPT_DIR%"
set "search_extensions=%SUBTITLE_EXTENSIONS%"
set "search_dir=%SCRIPT_DIR%"
call :search_video_dir

::если видеодир все еще не найдена, завершаем скрипт
if !video_dir_found! equ 0 (
    echo Error. Video directory not found. Was checked "%SCRIPT_DIR%" and !count_search_video_dir! directories upper. Exit...
    pause
    exit
)
goto :EOF


:search_video_dir
if !video_dir_found! equ 0 (
    ::при первом поиске
    if !count_search_video_dir! equ 0 (
        :: первый вызов ф-ции поиска
        call :search_in_current_dir

        :: если директория не найдена увеличиваем счетчик поиска
        if !video_dir_found! equ 0 (
            set /a count_search_video_dir+=1
        )

    ) else (

        if !count_search_video_dir! lss %SEARCH_LIMIT% (
            cd ..
            call :search_in_current_dir
            set /a count_search_video_dir+=1

        ) else (
            goto :EOF
        )
    )

    goto :search_video_dir
)
goto :EOF



:search_subtitle_dir
::ищем сабы в директории скрипта
set "search_extensions=%SUBTITLE_EXTENSIONS%"
cd "%SCRIPT_DIR%"
call :search_file_with_search_ext_in_dir
if !file_with_search_ext_found! equ 1 (
    set "search_dir=%SCRIPT_DIR%"
    cd "%VIDEO_DIR%"
    call :search_in_current_dir
    if !subtitle_dir_found! equ 1 goto :EOF
)
::пробуем найти в поддиректориях по запросу
set "search_string=%SEARCH_STRING_SUB%"
cd "%SCRIPT_DIR%"
call :search_by_string_search
if !subtitle_dir_found! equ 1 goto :EOF
::пробуем найти в поддиректориях
call :search_in_subdirectories
if !subtitle_dir_found! equ 1 goto :EOF

::если видеодир равно скриптдир выходим
if "%VIDEO_DIR%"=="!SCRIPT_DIR!" (
    set "subtitle_dir_found_or_search_completed=1"
    goto :EOF
)

:: ищем сабы в видеодир
cd "%VIDEO_DIR%"
call :search_file_with_search_ext_in_dir
if !file_with_search_ext_found! equ 1 (
    set "search_dir=%VIDEO_DIR%"
    call :search_in_current_dir
    if !subtitle_dir_found! equ 1 goto :EOF
)
::пробуем найти в поддиректориях по запросу
call :search_by_string_search
if !subtitle_dir_found! equ 1 goto :EOF
::пробуем найти в поддиректориях
call :search_in_subdirectories

set "subtitle_dir_found_or_search_completed=1"
goto :EOF



:search_font_dir
set "start_search_font_dir=1"
set "search_string=%SEARCH_STRING_FONT%"
set "search_extensions=%FONT_EXTENSIONS%"

::пробуем найти в директории скрипта
cd "%SCRIPT_DIR%"
call :search_file_with_search_ext_in_dir
if !font_dir_found! equ 1 goto :EOF
::пробуем найти в поддиректориях по запросу
call :search_by_string_search
if !font_dir_found! equ 1 goto :EOF
::пробуем найти в поддиректориях
call :search_in_subdirectories
if !font_dir_found! equ 1 goto :EOF

::пробуем найти в директории субтитров
if "%SCRIPT_DIR%" neq "%SUBTITLE_DIR%" (
    cd "%SUBTITLE_DIR%"
    call :search_file_with_search_ext_in_dir
    if !font_dir_found! equ 1 goto :EOF
    ::пробуем найти в поддиректориях по запросу
    call :search_by_string_search
    if !font_dir_found! equ 1 goto :EOF
    ::пробуем найти в поддиректориях
    call :search_in_subdirectories
    if !font_dir_found! equ 1 goto :EOF
)

::пробуем найти в родительской директории сабов в поддиректориях по запросу
cd ..
call :search_by_string_search

goto :EOF


:search_file_with_search_ext_in_dir
set "file_with_search_ext_found=0"
set "search_completed=0"

for %%f in (*.*) do (
    :: выполняем пока поиск не завершен
    if !search_completed! equ 0 (
        set "ext=%%~xf"

        :: проверяем на расширения из шрифтов
        for %%e in (!search_extensions!) do (

            ::выполняем пока поиск не завершен
            if !search_completed! equ 0 (
                if /i "!ext!"==".%%e" (
                    set "file_with_search_ext_found=1"

                    ::если искали фонтдир
                    if !start_search_font_dir! equ 1 (
                        set "FONT_DIR=%CD%"
                        set "font_dir_found=1"
                    )
                    ::выходим из циклов
                    set "search_completed=1"
                )
            )
        )
    )
)
set "search_completed=0"
goto :EOF



:search_and_download_ffmpeg_ffprobe
::проверяем доступен ли ffmpeg из командной строки
where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    set "FFMPEG_EXE=ffmpeg"
    
    where ffprobe >nul 2>&1
    if %errorlevel% equ 0 (
        set "FFPROBE_EXE=ffprobe"
        goto :EOF
    )
)

if not exist "%FFMPEG_DIR%\ffmpeg.exe" (
    call :download_ffmpeg_ffprobe
)
if not exist "%FFMPEG_DIR%\ffprobe.exe" (
    call :download_ffmpeg_ffprobe
)
goto :EOF

:download_ffmpeg_ffprobe
echo ffmpeg or/and ffprobe not found. Do you want to download it? [y/N]
set /p "user_input=> "

:: обработка ввода пользователя
if /i "!user_input!" neq "yes" (
    if /i "!user_input!" neq "y" (
        echo Consent to download has not been obtained.
        call :suggest_install_ffmpeg_manually
    )
)

:: скачиваем файл
echo Downloading "%FFMPEG_SOURCE_URL%"...
powershell -Command "Invoke-WebRequest -Uri '%FFMPEG_SOURCE_URL%' -OutFile '%FFMPEG_SOURCE_ZIP%'"

:: проверяем успешность загрузки
if not exist "%FFMPEG_SOURCE_ZIP%" (
    call :suggest_install_ffmpeg_manually
)

:: распаковываем файл
echo Extracting "%FFMPEG_SOURCE_ZIP%" to "%FFMPEG_EXTRACT_DIR%"...
powershell -Command "Expand-Archive -Path '%FFMPEG_SOURCE_ZIP%' -DestinationPath '%FFMPEG_EXTRACT_DIR%'"

:: удаляем скачанный архив
del "%FFMPEG_SOURCE_ZIP%"

:: проверяем успешность распаковки
if errorlevel 1 (
    call :suggest_install_ffmpeg_manually
)

:: снова пробуем найти ffmpeg
if not exist "%FFMPEG_DIR%\ffmpeg.exe" (
    call :suggest_install_ffmpeg_manually
)
if not exist "%FFMPEG_DIR%\ffprobe.exe" (
    call :suggest_install_ffmpeg_manually
)

echo ffmpeg and ffprobe has been successfully downloaded and extracted.
goto :EOF

:suggest_install_ffmpeg_manually
echo Download ffmpeg failed. Please manually download it "%FFMPEG_SOURCE_URL%" and extract to "%FFMPEG_EXTRACT_DIR%" directory.
echo Path to ffmpeg.exe should be "%FFMPEG_DIR%\ffmpeg.exe". Path to ffprobe.exe should be "%FFMPEG_DIR%\ffprobe.exe"
echo Alternative you can add any directory with ffmpeg.exe and ffprobe.exe to system PATH. Exit...
pause
exit



:search_mkvtoolnix
::проверяем доступен ли mkvmerge из командной строки
where mkvmerge >nul 2>&1
if %errorlevel% equ 0 (
    set "MKVMERGE_EXE=mkvmerge"
    where mkvinfo >nul 2>&1
    if %errorlevel% equ 0 (
        set "MKVINFO_EXE=mkvinfo"
        where mkvextract >nul 2>&1
        if %errorlevel% equ 0 (
            set "MKVEXTRACT_EXE=mkvextract"
            goto :EOF
        )
    )
)

::проверяем доступен ли mkvmerge в стандартных директориях
if exist "%PROGRAMFILES%\MkvToolNix\mkvmerge.exe" (
    set "MKVMERGE_EXE=%PROGRAMFILES%\MkvToolNix\mkvmerge.exe"
    if exist "%PROGRAMFILES%\MkvToolNix\mkvinfo.exe" (
        set "MKVINFO_EXE=%PROGRAMFILES%\MkvToolNix\mkvinfo.exe"
        if exist "%PROGRAMFILES%\MkvToolNix\mkvextract.exe" (
            set "MKVEXTRACT_EXE=%PROGRAMFILES%\MkvToolNix\mkvextract.exe"
            goto :EOF
        )
    )
)
if exist "%PROGRAMFILES(x86)%\MkvToolNix\mkvmerge.exe" (
    set "MKVMERGE_EXE=%PROGRAMFILES(x86)%\MkvToolNix\mkvmerge.exe"
    if exist "%PROGRAMFILES(x86)%\MkvToolNix\mkvinfo.exe" (
        set "MKVINFO_EXE=%PROGRAMFILES(x86)%\MkvToolNix\mkvinfo.exe"
        if exist "%PROGRAMFILES(x86)%\MkvToolNix\mkvextract.exe" (
            set "MKVEXTRACT_EXE=%PROGRAMFILES(x86)%\MkvToolNix\mkvextract.exe"
            goto :EOF
        )
    )
)

:: если не найден mkvmerge
if not exist "%MKVTOOLNIX_DIR%\mkvmerge.exe" (
    echo mkvtoolnix not found. Please manually download it "%MKVTOOLNIX_SOURCE_URL%" and extract to "%MKVTOOLNIX_EXTRACT_DIR%" directory
    echo Path to mkvmerge.exe should be "%MKVTOOLNIX_DIR%\mkvmerge.exe". Also supported path "%PROGRAMFILES%\MkvToolNix\mkvmerge.exe" and "%PROGRAMFILES(x86)%\MkvToolNix\mkvmerge.exe"
    echo Alternative you can add any directory with mkvtoolnix.exe to system PATH. Exit...
    pause
    exit
)
goto :EOF



:execute_generate
cd "%VIDEO_DIR%"
set "search_dir=%SCRIPT_DIR%"

:: если найдена директория аудио
if !audio_dir_found! equ 1 (
    set "search_extensions=%AUDIO_EXTENSIONS%"
    call :search_in_current_dir

) else (
    set "search_extensions=%SUBTITLE_EXTENSIONS%"
    call :search_in_current_dir
)
goto :EOF



:success
pause
::удаляем временные файлы
if exist "%SCRIPT_DIR%\delete-temp-files.py" (
    python "%SCRIPT_DIR%\delete-temp-files.py" "%VIDEO_DIR%" >nul 2>&1
)
echo Execution completed successfully. !count_generated_file! files generated.
pause
exit



:search_by_string_search
::флаги выхода
if !start_search_font_dir! equ 0 (
    if !subtitle_dir_found! equ 1 goto :EOF
)
if !font_dir_found! equ 1 goto :EOF

set "search_completed=0"
set "foundDir="

for %%R in (!search_string!) do (
    if !search_completed! equ 0 (

        for /d %%D in (*) do (
            if !search_completed! equ 0 (
                echo "%%D" | findstr /i "%%R" >nul
                if not errorlevel 1 (
                    set "foundDir=%%D"
                    set "search_completed=1"
                )
            )
        )
    )
)
set "search_completed=0"

:: если не найдена директория выходим
if not defined foundDir goto :EOF

cd "!foundDir!"

:: вызываем поиск еще раз, т.к. надписи обычно вложены
call :search_by_string_search

::вызываем поиск в поддиректориях найденной по запросу директории
call :search_in_subdirectories

::ищем файл с нужным расширением
call :search_file_with_search_ext_in_dir
if !file_with_search_ext_found! equ 0 goto :EOF

:: если не найдена директория сабов
if !subtitle_dir_found! equ 0 (
    :: запускаем поиск сабов в директории
    set "search_dir=!CD!"
    cd "%VIDEO_DIR%"
    call :search_in_current_dir
    ::возвращаемся в директорию до вызова
    cd "!search_dir!"
)

::возвращаемся в директорию до перехода в найденную поддиректорию
cd ..
goto :EOF



:search_in_subdirectories
::флаги выхода
if !start_search_font_dir! equ 0 (
    if !subtitle_dir_found! equ 1 goto :EOF
)
if !font_dir_found! equ 1 goto :EOF

set "search_completed=0"
:: Iterate over all subdirectories in the current directory
for /d %%D in (*) do (

    if !search_completed! equ 0 (
        :: если поддиректория существует
        if exist "%%D" (

            :: переходим в найденную поддиректорию
            cd "%%D"

            :: в найденной поддиректории пробуем найти поддиректории по запросу
            call :search_by_string_search

            ::вызываем поиск в поддиректориях
            call :search_in_subdirectories

            ::ищем файл с нужным расширением
            call :search_file_with_search_ext_in_dir
            if !file_with_search_ext_found! equ 1 (
                :: если не найдена директория сабов
                if !subtitle_dir_found! equ 0 (
                    :: запускаем поиск сабов в текущей директории
                    set "search_dir=!CD!"
                    cd "%VIDEO_DIR%"
                    call :search_in_current_dir
                    ::возвращаемся
                    cd "!search_dir!"

                    if !subtitle_dir_found! equ 1 (
                        set "search_completed=1"
                    )
                )
            )
            if !font_dir_found! equ 1 (
                set "search_completed=1"
            )

            ::возвращаемся в директорию до перехода в найденную поддиректорию
            cd ..
        )
    )
)
::возвращаем значение
set "search_completed=0"
goto :EOF



:: поиск в директории
:search_in_current_dir
::флаг завершения поиска
set "search_completed=0"

for %%f in (*.*) do (

    :: выполняем только если поиск не завершен
    if !search_completed! equ 0 (
        set "file1_name=%%~nf"
        set "ext1=%%~xf"

        set "video_found=0"

        :: проверяем на расширения из видеорасширений
        for %%e in (%VIDEO_EXTENSIONS%) do (

            :: выполняем только если видео еще не найдено
            if !video_found! equ 0 (

                :: выполняем если файл имеет видеорасширение
                if /i "!ext1!"==".%%e" (
                    set "video_file=%VIDEO_DIR%\%%f"
                    set "current_dir=!CD!"
                    call :search_file2

                    :: выполняем только если файл2 найден
                    if !file2_found! equ 1 (
                        set "current_check_ext=!ext2!"

                        if !video_dir_found! equ 0 (
                            call :check_video_dir_found

                        ) else (
                            if !subtitle_dir_found_or_search_completed! equ 0 (
                                call :subtitle_dir_found

                            ) else (
                                call :audio_or_subtitle_found
                            )
                        )
                    )
                )
            )
        )
    )
)
goto :EOF


:: поиск в директории
:search_file2
cd "!search_dir!"
set "file2_found=0"

::флаг завершения поиска
set "search_completed=0"

for %%f in (*.*) do (
    :: выполняем только если поиск не завершен
    if !search_completed! equ 0 (
        set "file2_name=%%~nf"
        set "ext2=%%~xf"

        :: проверяем на расширения из искомых расширений
        for %%e in (!search_extensions!) do (

            :: выполняем только если файл2 еще не найден
            if !file2_found! equ 0 (

                :: выполняем если файл имеет искомое расширение
                if /i "!ext2!"==".%%e" (

                    echo "!file1_name!" | findstr /C:"!file2_name!" >nul
                    if !errorlevel! equ 0 (

                        :: проверить что имена видео и файла не содержат _replaced_
                        call :check_specific_replaced_name
                    )

                    echo "!file2_name!" | findstr /C:"!file1_name!" >nul
                    if !errorlevel! equ 0 (

                        :: проверить что имена видео и файла2 не содержат _replaced_
                        call :check_specific_replaced_name
                    )
                )
            )
        )
    )
)
:: сбрасываем флаг
set "search_completed=0"

cd "!current_dir!"
goto :EOF

:check_specific_replaced_name
::проверять видео есть смысл только если видео в директории скрипта
if !count_search_video_dir! equ 0 (
    :: выходим если имя видеофайла служебное
    echo "!file1_name!" | findstr /C:"_replaced_" >nul
    if !errorlevel! equ 0 (
        goto :EOF
    )
)
echo "!file2_name!" | findstr /C:"_replaced_" >nul
if !errorlevel! equ 0 (
    goto :EOF
)
set "search_file=!search_dir!\!file2_name!!ext2!"
set "file2_found=1"
set "search_completed=1"
goto :EOF



:check_video_dir_found
::если зашли сюда через найденный файл саба идем в video_dir_found
if !start_search_video_dir_from_subtitle! equ 1 goto :video_dir_found

::если найденный файл равно видеофайлу выходим
if "!search_file!"=="!video_file!" goto :EOF

::если в директории скрипта
if !count_search_video_dir! equ 0 (
    call :check_mix_extensions

    ::если у файла есть видеодорожка
    if !file_have_video_track! equ 1 (
        call :video_dir_found
    )

) else (
    call :video_dir_found
)
goto :EOF

:video_dir_found
set "VIDEO_DIR=%CD%"
set "video_dir_found=1"

::если зашли сюда через найденный файл саба идем в subtitle_dir_found
if !start_search_video_dir_from_subtitle! equ 1 goto :subtitle_dir_found

set "audio_dir_found=1"

::флаги для выхода из цикла
set "search_completed=1"
set "video_found=1"
goto :EOF



:subtitle_dir_found
set "SUBTITLE_DIR=!search_dir!"
set "subtitle_dir_found=1"
set "subtitle_dir_found_or_search_completed=1"
cd "%VIDEO_DIR%"

::флаги для выхода из циклов for
set "search_completed=1"
set "video_found=1"
goto :EOF



:audio_or_subtitle_found
::если найденный файл равно видеофайлу выходим
if "!search_file!" == "!video_file!" goto :EOF

if !audio_dir_found! equ 1 (
    set "audio_file=!search_file!"
) else (
    set "subtitle_file=!search_file!"
)

:: если директория субтитров не найдена
if !subtitle_dir_found! equ 0 (
    :: если видеодиректория в директории скрипта
    if !count_search_video_dir! equ 0 (
        call :check_mix_extensions
        :: если не обнаружено отсутствие видеодорожки в видеоконтейнере
        if !file_have_video_track! equ 1 (
            call :ffmpeg_replace_audio
        )
    ) else (
        ::если видеодиректория не в директории скрипта просто заменяем аудиодорожку без доп проверок
        call :ffmpeg_replace_audio
    )
) else (
    ::если сабдир найдена
    if !audio_dir_found! equ 0 (
        ::если фонтдир не найдена
        if !font_dir_found! equ 0 (
            call :ffmpeg_replace_sub
        ) else (
            call :mkvmerge_replace_sub_add_font
        )
    ) else (
        :: если видеодиректория в директории скрипта
        if !count_search_video_dir! equ 0 (
            call :check_mix_extensions
            :: если не обнаружено отсутствие видеодорожки в видеоконтейнере
            if !file_have_video_track! equ 1 (
                call :search_subtitle
                :: если найден сабфайл
                if !subtitle_found! equ 1 (
                    :: если найден фонтдир
                    if !font_dir_found! equ 1 (
                        call :mkvmerge_replace_audio_replace_sub_add_font
                    ) else (
                        call :ffmpeg_replace_audio_replace_sub
                    )
                ) else (
                    ::сабфайл не найден
                    call :ffmpeg_replace_audio
                )
            )
        ) else (
            call :search_subtitle
            :: если найден сабфайл
            if !subtitle_found! equ 1 (
                :: если найден фонтдир
                if !font_dir_found! equ 1 (
                    call :mkvmerge_replace_audio_replace_sub_add_font
                ) else (
                    call :ffmpeg_replace_audio_replace_sub
                )
            ) else (
                ::сабфайл не найден
                call :ffmpeg_replace_audio
            )
        )
    )
)
:: возвращаемся в цикл поиска аудио для видеофайлов
goto :EOF


:check_mix_extensions
:: по умолчанию считаем что видеодорожка есть
set "file_have_video_track=1"

:: если расширение аудио чисто аудио, то не надо проверять
set "check_extensions=%MIX_EXTENSIONS%"
call :check_compliance_extension
:: если расширение аудио не смешанное выходим
if !compliance_extension! equ 0 (
    goto :EOF
)

::проверка расширения видео
set "current_check_ext=!ext1!"
call :check_compliance_extension

:: если расширение видео смешанное
if !compliance_extension! equ 1 (

    ::проверяем наличие видеодорожки
    call :check_video_track
)

goto :EOF



:search_subtitle
set "subtitle_found=0"
set "search_dir=%SUBTITLE_DIR%"
set "search_extensions=%SUBTITLE_EXTENSIONS%"
set "current_dir=!CD!"
call :search_file2

if !file2_found! equ 1 (
    set "subtitle_file=!search_file!"
    set "subtitle_found=1"
)

::возвращаем флаги
set "search_extensions=%AUDIO_EXTENSIONS%"
set "search_dir=%SCRIPT_DIR%"
set "file2_found=1"
goto :EOF

:run_python_generate_from_chapters
if "!ext1!" neq ".mkv" goto :EOF
set "chapters_file=%VIDEO_DIR%\temp_chapters.xml"
::удаляем chapters от предыдущего видео если есть
if exist "!chapters_file!" (
    del "!chapters_file!"
)
::пробуем извлечь chapters из video
"%MKVEXTRACT_EXE%" "!video_file!" chapters "!chapters_file!" >nul 2>&1
::выходим если нет chapters или скрипта
if not exist "!chapters_file!" goto :EOF
if not exist "%SCRIPT_DIR%\merge-video-from-split-chapters.py" goto :EOF

:: если создан фонтлист
if !font_attach_list_created! equ 1 (
    set "font_list_txt=%VIDEO_DIR%\temp_font_list.txt"
    if not exist "font_list_txt" (
        echo "!font_attach_list!" > "!font_list_txt!"
    )
)
python "%SCRIPT_DIR%\merge-video-from-split-chapters.py" "%MKVINFO_EXE%" "%MKVMERGE_EXE%" "!output_file!" "%VIDEO_DIR%" "!video_file!" "!chapters_file!" "%audio_file%" "!subtitle_file!" "!font_dir!" "!font_list_txt!"
goto :EOF

:ffmpeg_replace_audio_replace_sub
set "output_file=%SCRIPT_DIR%\!file1_name!_replaced_audio_replaced_sub.mkv"
::если выходной файл с таким именем существует выходим
if exist "!output_file!" (
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)
call :run_python_generate_from_chapters
if exist "!output_file!" (
    set /a count_generated_file+=1
    if !count_generated_file! geq %FILE_LIMIT% call :success
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)

echo Replacing audio track of "!video_file!" with the audio track of "!audio_file!", adding or replacing the subtitle "!subtitle_file!" and saving result to "!output_file!"
"%FFMPEG_EXE%" -i "!video_file!" -i "!audio_file!" -i "!subtitle_file!" %FFMPEG_PARAMS_AUDIO_SUB% "!output_file!" >nul 2>&1
set /a count_generated_file+=1

:: если количество сгенерированных файлов больше или равно лимиту вызываем завершающую ф-цию
if !count_generated_file! geq %FILE_LIMIT% call :success

set "subtitle_found=0"
:: флаги выхода
set "video_found=1"
goto :EOF



:ffmpeg_replace_audio
call :set_extension_output_file
set "output_file=%SCRIPT_DIR%\!file1_name!_replaced_audio!output_file_extension!"
::если выходной файл с таким именем существует выходим
if exist "!output_file!" (
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)
call :run_python_generate_from_chapters
if exist "!output_file!" (
    set /a count_generated_file+=1
    if !count_generated_file! geq %FILE_LIMIT% call :success
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)


echo Replacing audio track of "!video_file!" with the audio track of "!audio_file!" and saving result to "!output_file!"
"%FFMPEG_EXE%" -i "!video_file!" -i "!audio_file!" %FFMPEG_PARAMS_AUDIO_ONLY% "!output_file!" >nul 2>&1
set /a count_generated_file+=1

:: если количество сгенерированных файлов больше или равно лимиту вызываем завершающую ф-цию
if !count_generated_file! geq %FILE_LIMIT% call :success

:: флаг выхода
set "video_found=1"
goto :EOF


:ffmpeg_replace_sub
set "output_file=%SCRIPT_DIR%\!file1_name!_replaced_sub.mkv"
::если выходной файл с таким именем существует выходим
if exist "!output_file!" (
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)
call :run_python_generate_from_chapters
if exist "!output_file!" (
    set /a count_generated_file+=1
    if !count_generated_file! geq %FILE_LIMIT% call :success
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)

echo Adding or replacing subtitle track "!subtitle_file!" to "!video_file!" and saving result to "!output_file!"
"%FFMPEG_EXE%" -i "!video_file!" -i "!subtitle_file!" %FFMPEG_PARAMS_SUB_ONLY% "!output_file!" >nul 2>&1
set /a count_generated_file+=1

:: если количество сгенерированных файлов больше или равно лимиту вызываем завершающую ф-цию
if !count_generated_file! geq %FILE_LIMIT% call :success

set "subtitle_found=0"
:: флаг выхода
set "video_found=1"
goto :EOF


:set_extension_output_file
::проверить что расширение исходного видео соответствует расширениям с поддержкой аудио и видео
set "current_check_ext=!ext1!"
set "check_extensions=%MIX_EXTENSIONS%"
call :check_compliance_extension

::если контейнер поддерживает аудио оставляем его иначе ставим .mvk
if !compliance_extension! equ 1 (
    set "output_file_extension=!current_check_ext!"

) else (
    set "output_file_extension=.mkv"
)
goto :EOF



:check_compliance_extension
set "compliance_extension=0"

for %%c in (!check_extensions!) do (

    if /i "!current_check_ext!"==".%%c" (
        set "compliance_extension=1"
    )
)
goto :EOF


:mkvmerge_replace_audio_replace_sub_add_font
set "output_file=%SCRIPT_DIR%\!file1_name!_replaced_audio_replaced_sub_added_font.mkv"
::если выходной файл с таким именем существует выходим
if exist "!output_file!" (
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)
call :run_python_generate_from_chapters
if exist "!output_file!" (
    set /a count_generated_file+=1
    if !count_generated_file! geq %FILE_LIMIT% call :success
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)

cd "%FONT_DIR%"
echo Replacing audio track of "!video_file!" with the audio track of "!audio_file!", adding or replacing subtitle "!subtitle_file!", attach the fonts and saving result to "!output_file!". Attach fonts: !font_attach_list!
"%MKVMERGE_EXE%" -o "!output_file!" -a 0 -s 0 "!video_file!" -a 0 "!audio_file!" -s 0 "!subtitle_file!" !font_attach_list! >nul 2>&1
set /a count_generated_file+=1

:: если количество сгенерированных файлов больше или равно лимиту вызываем завершающую ф-цию
if !count_generated_file! geq %FILE_LIMIT% call :success

cd "%VIDEO_DIR%"
set "subtitle_found=0"
:: флаг выхода
set "video_found=1"
goto :EOF

:mkvmerge_replace_sub_add_font
set "output_file=%SCRIPT_DIR%\!file1_name!_replaced_sub_added_font.mkv"
::если выходной файл с таким именем существует выходим
if exist "!output_file!" (
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)
call :run_python_generate_from_chapters
if exist "!output_file!" (
    set /a count_generated_file+=1
    if !count_generated_file! geq %FILE_LIMIT% call :success
    call :set_exit_flags_when_output_file_already_exist
    goto :EOF
)

cd "%FONT_DIR%"
echo Adding or replacing subtitle track "!subtitle_file!" and attach the fonts to "!video_file!" and saving result to "!output_file!". Attach fonts: !font_attach_list!
"%MKVMERGE_EXE%" -o "!output_file!" -s 0 "!video_file!" -s 0 "!subtitle_file!" !font_attach_list! >nul 2>&1
set /a count_generated_file+=1

:: если количество сгенерированных файлов больше или равно лимиту вызываем завершающую ф-цию
if !count_generated_file! geq %FILE_LIMIT% call :success

cd "%VIDEO_DIR%"
set "subtitle_found=0"
:: флаг выхода
set "video_found=1"
goto :EOF


:set_exit_flags_when_output_file_already_exist
set "subtitle_found=0"
set "video_found=1"
goto :EOF


:create_font_attach_list
set font_attach_list=

:: Добавление всех шрифтов в список
for %%F in (*.ttf *.otf) do (
    echo %%F>> temp_font_list.txt
)

:: Проверка наличия файлов для обработки
if not exist temp_font_list.txt (
    goto :EOF
)

:: Чтение списка файлов и добавление их в attach_list
for /f "tokens=*" %%l in (temp_font_list.txt) do (
    set font_attach_list=!font_attach_list! --attach-file "%%l"
)
set "font_attach_list_created=1"
del temp_font_list.txt
goto :EOF


:check_video_track
set ffprobe_output=
set "file_have_video_track=1"
:: запись вывода ffprobe в файл
"%FFPROBE_EXE%" %FFPROBE_PARAMS% "!video_file!" > temp_txt.txt
:: Чтение вывода из временного файла в переменную
set /p ffprobe_output=<temp_txt.txt

:: Удаление временного файла
del temp_txt.txt

:: если в файле нет видеодорожки
if "!ffprobe_output!" neq "video" (
    set "file_have_video_track=0"
)

goto :EOF


endlocal

