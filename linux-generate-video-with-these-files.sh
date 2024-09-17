#!/bin/sh

# Расширения для аудио и видео файлов
AUDIO_EXTENSIONS="mka m4a mp4 aac ac3 flac mp3 ogg opus mov flv"
VIDEO_EXTENSIONS="mkv mp4 avi m4a mpeg mpg ts webm mov flv"
# Расширения требующие дополнительной проверки
MIX_EXTENSIONS="mkv mp4 avi webm mov flv"

# Параметры обработки ffmpeg
FFMPEG_PARAMS="-c:v copy -c:a copy -map 0:v:0 -map 1:a:0"
# Параметры проверки через ffprobe на наличие видеодорожки
FFPROBE_PARAMS="-v error -select_streams v:0 -show_entries stream=codec_type -of default=noprint_wrappers=1:nokey=1"

# Определяем директорию скрипта
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# Сколько директорий над директорией скрипта проверяется на наличие видео
SEARCH_LIMIT=3

# Запрашиваем у пользователя количество обрабатываемых файлов
read -p "Enter the number of files to process (or press Enter to process all files): " FILE_LIMIT

# Устанавливаем значение по умолчанию для FILE_LIMIT, если ввод пустой или некорректный
if [[ ! "$FILE_LIMIT" =~ ^[0-9]+$ ]]; then
    FILE_LIMIT=999999
fi

# Переходим в директорию скрипта
cd "$SCRIPT_DIR" || exit

# Счетчик поиска видеодиректории
count_search_video_dir=0

# Счетчик обработанных файлов
count_processed_file=0



# Проверяем, установлен ли ffmpeg
if ! command -v ffmpeg > /dev/null 2>&1; then
    echo "ffmpeg not found. Exit..."
    exit 1
fi


# Функция для успешного завершения
success() {
    echo "Processing completed successfully. $count_processed_file files processed"
    exit 0
}


# Функция для замены аудиодорожки
replace_audio_track() {
    local video_file="$1"
    local audio_file="$2"
    local output_file="$3"

    echo "Replacing audio track of '$video_file' with the audio track of '$audio_file' and saving result to '$output_file'"

    ffmpeg -i "$video_file" -i "$audio_file" $FFMPEG_PARAMS "$output_file"
    ((count_processed_file++))

    # Если количество обработанных файлов больше или равно лимиту вызываем завершающую функцию
    if ((count_processed_file >= FILE_LIMIT)); then
        success
    fi
}


# Функция для проверки наличия видеодорожки
check_video_track() {
    local video_file="$1"
    local ffprobe_output

    # Запись вывода ffprobe в переменную
    ffprobe_output=$(ffprobe $FFPROBE_PARAMS "$video_file" 2>&1)

    # Если в файле нет видеодорожки
    if [[ "$ffprobe_output" != "video" ]]; then
        echo "Container '$video_file' does not have a video track"
        return 1
    fi
    return 0
}


# Функция поиска и сопоставления файлов
search_and_match_files() {
    local current_dir="$1"
    local video_file
    local audio_file
    local audio_found
    local file_name
    local ext

    # Поиск видеофайлов и сопоставление с аудиофайлами
    for video_file in "$current_dir"/*; do
        file_name=$(basename "$video_file")
        ext="${file_name##*.}"

        # Проверяем, если это видеофайл
        if [[ " $VIDEO_EXTENSIONS " == *" $ext "* ]]; then
            audio_found=0

            # Пробуем найти соответствующий аудиофайл
            for audio_ext in $AUDIO_EXTENSIONS; do
                audio_file="$SCRIPT_DIR/${file_name%.*}.$audio_ext"

                # Если существует аудиофайл
                if [[ -e "$audio_file" ]]; then
                    audio_found=1

                    # Если видеодиректория в директории скрипта
                    if ((count_search_video_dir == 0)); then
                        # По умолчанию считаем что видеодорожка есть
                        file_have_video_track=1

                        # Проверка на смешанные расширения
                        for mix_ext in $MIX_EXTENSIONS; do
                            if [[ "$ext" == "$mix_ext" ]]; then
                                # Проверяем наличие видеодорожки
                                check_video_track "$video_file" || file_have_video_track=0
                            fi
                        done

                        # Если не обнаружено отсутствие видеодорожки в видеоконтейнере
                        if ((file_have_video_track == 1)); then
                            # Если видеодиректория не найдена устанавливаем видеодиректорию
                            if ((video_dir_found == 0)); then
                                video_dir_found=1
                                video_dir="$current_dir"
                                return
                            # а если найдена заменяем аудио
                            else
                                output_file="$SCRIPT_DIR/${file_name%.*}_replaced_audio.$ext"
                                replace_audio_track "$video_file" "$audio_file" "$output_file"
                            fi
                        fi

                    else
                        # Если видеодиректория не найдена устанавливаем видеодиректорию
                        if ((video_dir_found == 0)); then
                            video_dir_found=1
                            video_dir="$current_dir"
                            return
                        # а если найдена заменяем аудио
                        else
                            output_file="$SCRIPT_DIR/${file_name%.*}_replaced_audio.$ext"
                            replace_audio_track "$video_file" "$audio_file" "$output_file"
                        fi
                    fi
                fi
            done

            # Если подходящее аудио не найдено
            if ((audio_found == 0)); then
                echo "Audio file for video file '$video_file' not found."
            fi
        fi
    done
}


# Функция для поиска видеодиректории
search_video_dir() {
    video_dir_found=0
    local current_dir="$PWD"

    # Поиск видеодиректории
    while ((video_dir_found == 0)); do
        search_and_match_files "$current_dir"

        # если видеодиректория найдена выходим из функции
        if ((video_dir_found == 1)); then
            return
        fi

        if ((count_search_video_dir == SEARCH_LIMIT)); then
            echo "Error. Video directory not found. Was checked '$SCRIPT_DIR' and $count_search_video_dir directories up. Exit..."
            exit 1
        fi

        cd ..
        ((count_search_video_dir++))
        current_dir="$PWD"
    done
}

# Вызов ф-ции поиска видеодиректории
search_video_dir
search_and_match_files "$video_dir"
success
