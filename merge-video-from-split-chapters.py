"""
merge-video-from-split-chapters-v0.3.2
This program is part of the generate-video-with-these-files-script repository
Licensed under GPL-3.0. See LICENSE file for details.
Author: nujievik Email: nujievik@gmail.com
"""
import sys
import xml.etree.ElementTree as ET
import os
import shutil
import re
import subprocess
import shlex
from pathlib import Path
from datetime import timedelta

def timedelta_to_str(td):
    #Конвертирует timedelta в строку времени с двумя знаками после точки
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int(td.microseconds / 1000)
    return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds // 10:02}"  # Два знака после точки

def str_to_timedelta(time_str):
    hours, minutes, seconds = time_str.split(':')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return timedelta(seconds=total_seconds)

def write_lines_to_file(filename, *args):
    # Записываем переменные в файл
    with open(filename, 'w', encoding='utf-8') as file:
        for line in args:
            file.write(f"{line}\n")
    #print(f"Data written to the file {filename}")

def add_lines_to_file(filename, *args):
    # Добавляем переменные в файл
    with open(filename, 'a', encoding='utf-8') as file:
        for line in args:
            file.write(f"{line}\n")
    #print(f"Data added to the file {filename}")

def read_lines_from_file(filename, num_lines):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        # Проверяем, что в файле достаточно строк
        if len(lines) >= num_lines:
            return [line.strip() for line in lines[:num_lines]]
        else:
            #print(f"Error. File '{filename}' not have enough lines")
            return None

    except FileNotFoundError:
        #print(f"File '{filename}' not found")
        return None

def read_write_uid_file_params(uid, directory, start_split, time_start, time_end):
    #print(f"debug UID: {uid}")
    # Пробуем считать данные из txt
    temp_txt_uid_split = Path(directory) / f"temp_{uid}.txt"
    #print(f"DEBUG temp text file: {temp_txt_uid_split}")
    needed_segment = None
    segment_length = None
    offset_start = None
    offset_end = None
    read = read_lines_from_file(temp_txt_uid_split, 6)
    if read:
        line1, line2, line3, line4, line5, line6 = read
        #print(line1, line2, line3, line4, line5, line6)
        video_for_processing = line1
        #если время предыдущего сплита совпадает
        if str_to_timedelta(line2) == time_start and (str_to_timedelta(line3) == time_end or str_to_timedelta(line4) <= time_end):
            #print("DEBUG line2 equ time_start and (line3 equ time_end or line4 <= time_end")
            #и нужный сплит существует не сплитуем
            needed_segment = Path (directory) / f"temp_{uid}.mkv"
            if needed_segment.exists():
                #print("DEBUG set dont split flag")
                segment_length = str_to_timedelta(line4)
                offset_start = str_to_timedelta(line5)
                offset_end = str_to_timedelta(line6)
                start_split = False
    else:
        #print("DEBUG read temtxt failure")
        video_for_processing = find_video_file_with_uid(directory, uid)
        write_lines_to_file(temp_txt_uid_split, video_for_processing, time_start, time_end)

    return temp_txt_uid_split, video_for_processing, start_split, needed_segment, segment_length, offset_start, offset_end

def get_file_info(filepath, search_query):
    try:
        mkvinfo_stdout = subprocess.run([mkvinfo.as_posix(), filepath], capture_output=True, text=True, check=True).stdout
        #print(mkvinfo_stdout)

        for line in mkvinfo_stdout.splitlines():
            #print(f"DEBUG line: '{line}'")
            if search_query in line:
                if "Segment UID" in search_query:
                    uid_hex = line.split(":")[-1].strip()
                    # Преобразуем в строку формата 93828424aeb8a27a942fb070d17459f8
                    uid_clean = "".join(byte[2:] for byte in uid_hex.split() if byte.startswith("0x"))
                    return uid_clean

                if "Duration" in search_query:
                    match = re.search(r'Duration:\s*(.*)', line)  # Находим всю часть после 'Duration:'
                    if match:
                        file_duration = match.group(1).strip()  # Убираем пробелы
                        file_duration_timedelta = str_to_timedelta(file_duration)
                        #print(f"DEBUG file duration: '{file_duration_timedelta}'")
                        return file_duration_timedelta
    except subprocess.CalledProcessError as e:
        print(f"Error when execute mkvinfo for file '{filepath}': {e}")
    return None

def find_video_file_with_uid(directory, target_uid):
    for filename in os.listdir(directory):
        if filename.lower().endswith(".mkv"):
            filepath = os.path.join(directory, filename)
            file_uid = get_file_info(filepath, "Segment UID")
            #print(f"DEBUG fileuid: {file_uid}")
            if file_uid.lower() == target_uid.lower(): #сравниваем uid в одном регистре
                return filepath
    return None
    
def get_needed_segment_info(mkvmerge_stdout, output_partname, split_time_start, split_time_end):
    #ищем переназначения
    timestamps = re.findall(r'Timestamp used in split decision: (\d{2}:\d{2}:\d{2}\.\d{9})', mkvmerge_stdout)
    if len(timestamps) == 2:
        needed_segment = Path(output_partname.parent) / f"{output_partname.stem}-002{output_partname.suffix}"
        defacto_time_start = str_to_timedelta(timestamps[0])
        defacto_time_end = str_to_timedelta(timestamps[1])
        offset_start = defacto_time_start - split_time_start
        offset_end = defacto_time_end - split_time_end
    elif len(timestamps) == 1:
        timestamp = str_to_timedelta(timestamps[0])
        #если переназначение для старта
        if split_time_start > timedelta(0):
            needed_segment = Path(output_partname.parent) / f"{output_partname.stem}-002{output_partname.suffix}"
            defacto_time_start = timestamp
            defacto_time_end = defacto_time_start + get_file_info(needed_segment, search_query="Duration")
            offset_start = defacto_time_start - split_time_start
            offset_end = timedelta(0) #время указанное для сплита выходит за границы файла; реально воспроизводится только то что в границах файла
        else:
            needed_segment = Path(output_partname.parent) / f"{output_partname.stem}-001{output_partname.suffix}"
            defacto_time_start = timedelta(0)
            defacto_time_end = timestamp
            offset_start = timedelta(0)
            offset_end = defacto_time_end - split_time_end
    else:
        needed_segment = Path(output_partname.parent) / f"{output_partname.stem}-001{output_partname.suffix}"
        defacto_time_start = timedelta(0)
        defacto_time_end = get_file_info(needed_segment, search_query="Duration")
        offset_start = timedelta(0)
        offset_end = timedelta(0)

    #print(f"DEBUG needed_segment {needed_segment} defacto start {defacto_time_start} defacto end {defacto_time_end} offset_start {offset_start} offset_end {offset_end}")
    return needed_segment, defacto_time_start, defacto_time_end, offset_start, offset_end

def split_file(input_file, output_partname, time_start, time_end, total_length, a_total_length=[], file_type="video", repeat_split=False, save_original_audio=False):
    command = [mkvmerge.as_posix(), "-o", f"{output_partname}", "--split", f"timecodes:{time_start},{time_end}", "--no-global-tags", "--no-chapters", "--no-subtitles", "--no-attachments"]
    if "video" in file_type:
        command.append("--no-audio")
    else:
        command.append("--no-video")
    command.append(f"{input_file}")
    #print(f"DEBUG command {command}")

    # Выполняем команду и ищем переназначения
    mkvmerge_stdout = subprocess.run(command, capture_output=True, text=True).stdout
    #print(mkvmerge_stdout)
    needed_segment, defacto_time_start, defacto_time_end, offset_start, offset_end = get_needed_segment_info(mkvmerge_stdout, output_partname, time_start, time_end)
    if repeat_split:
        #если переназначения >0.2 секунд пытаемся сдвинуться назад на эти значения и снова сплитнуть
        if offset_start > timedelta(seconds=0.2) or offset_end > timedelta(seconds=0.2):
            new_time_start = time_start - offset_start if time_start - offset_start >= timedelta(0) else time_start
            new_time_end = time_end - offset_end
            needed_segment, segment_length, temp_offset_start, temp_offset_end = split_file(input_file, output_partname, new_time_start, new_time_end, total_length, None, file_type)
            offset_start = offset_start - temp_offset_start
            offset_end = offset_end - temp_offset_end
            #print(f"DEBUG defacto start {defacto_time_start} defacto_time_end {defacto_time_end} segment_length {segment_length}")
        else:
            segment_length = defacto_time_end - defacto_time_start
    else:
        segment_length = defacto_time_end - defacto_time_start
        #print(f"DEBUG defacto start {defacto_time_start} defacto_time_end {defacto_time_end} segment_length {segment_length}")

    if save_original_audio and not repeat_split:
        #print(f"DEBUG save_original_audio in split_file")
        a_output_partname = Path(output_partname.parent) / f"{output_partname.stem}.mka"
        a_needed_segment = Path(needed_segment.parent) / f"{needed_segment.stem}.mka"
        #дельта между аудио и видео до текущего сплита - офсет для аудио старт
        offset_a_start = total_length - a_total_length
        #print(f"DEBUG offset_a_start: {offset_a_start}")
        new_time_start = defacto_time_start - offset_a_start if defacto_time_start - offset_a_start >= timedelta(0) else defacto_time_start
        a_needed_segment, a_segment_length, *_ = split_file(input_file, a_output_partname, new_time_start, defacto_time_end, a_total_length, None, file_type="audio", repeat_split=True, save_original_audio=False)
        return needed_segment, segment_length, offset_start, offset_end, a_needed_segment, a_segment_length
    #print(f"DEBUG return needed_segment: {needed_segment}, segment_length: {segment_length}, offset_start: {offset_start}, offset_end: {offset_end}")
    return needed_segment, segment_length, offset_start, offset_end

def set_split_partname(directory, count, time_start, ext):
    # устанавливаем начало имени сплитов
    split_partname = Path (directory) / f"temp_{count}.{ext}"
    return split_partname
    
def get_linked_segment(directory, video_file, file_uid, time_start, time_end, previous_nonuid_time_end, count, total_length, total_offset_end, save_original_audio=False, a_total_length=None):
    start_split = True
    chapter_time_start = time_start
    chapter_time_end = time_end
    split_partname = set_split_partname(directory, count, time_start, ext="mkv")
        
    # если uid пуст сплитуем текущее видео
    if file_uid is None:
        #print("DEBUG UID is missing")
        file_to_be_split = video_file
        time_start = previous_nonuid_time_end
    else:
        temp_txt_uid_split, file_to_be_split, start_split, needed_segment, segment_length, offset_start, offset_end = read_write_uid_file_params(file_uid, directory, start_split, time_start, time_end)
    #print(f"DEBUG split video: {file_to_be_split}")
        
    # сплитуем если нужно
    if start_split:
        #print(f"DEBUG start split video.")
        previous_total_length = total_length
        if save_original_audio:
            needed_segment, segment_length, offset_start, offset_end, a_needed_segment, a_segment_length = split_file(file_to_be_split, split_partname, time_start, time_end, total_length, a_total_length, file_type="video", repeat_split=False, save_original_audio=True)
            a_total_length = a_total_length + a_segment_length
        else:
            needed_segment, segment_length, offset_start, offset_end = split_file(file_to_be_split, split_partname, time_start, time_end, total_length)
        total_length = total_length + segment_length
        
        # если сплит по внешнему файлу переименовываем его чтоб использовать дальше
        if file_uid is not None:
            new_name_needed_segment = Path (directory) / f"temp_{file_uid}.mkv"
            #print(f"DEBUG chapter segment uid is not None. new split name: {new_name_needed_segment}")
            #если файл уже есть удаляем
            if os.path.exists(new_name_needed_segment): 
                os.remove(new_name_needed_segment)
            os.rename(needed_segment, new_name_needed_segment)
            needed_segment = new_name_needed_segment
            #записываем длину файла и офсеты
            add_lines_to_file(temp_txt_uid_split, total_length - previous_total_length, offset_start, offset_end)

    else:
        total_length = total_length + segment_length
        if save_original_audio:
            a_split_partname = Path(split_partname.parent) / f"{split_partname.stem}.mka"
            #a_split_partname = set_split_partname(directory, count, time_start, ext="mka")
            offset_a_start = total_length - segment_length - a_total_length
            #print(f"DEBUG offset_a_start: {offset_a_start}")
            new_time_start = time_start - offset_a_start if time_start - offset_a_start >= timedelta(0) else time_start
            a_needed_segment, a_segment_length, *_ = split_file(file_to_be_split, a_split_partname, new_time_start, time_end, a_total_length, None, file_type="audio", repeat_split=True, save_original_audio=False)
            a_total_length = a_total_length + a_segment_length
            #print(f"DEBUG a_total_length: {a_total_length}")

    if file_uid is None:
        total_offset_start = offset_start
        total_offset_end = (time_end - chapter_time_end) + offset_end
        previous_nonuid_time_end = chapter_time_end + offset_end
    else:
        total_offset_start = total_offset_end + offset_start
        total_offset_end = total_offset_end + offset_end
    #print(f"DEBUG total_length: {total_length} \ntotal_offset_start: {total_offset_start} \ntotal_offset_end: {total_offset_end}")

    if save_original_audio:
        return needed_segment, previous_nonuid_time_end, total_length, total_offset_start, total_offset_end, a_needed_segment, a_total_length
    else:
        return needed_segment, previous_nonuid_time_end, total_length, total_offset_start, total_offset_end

def parse_chapters_file(chapters_file, directory, video_file, check_exist_ext_file=False, save_original_audio=False):
    tree = ET.parse(chapters_file)
    root = tree.getroot()

    count = 0
    merge_list = []
    lengths_list = []
    offsets_start_list = []
    offsets_end_list = []
    total_length = timedelta(0)
    total_offset_start = timedelta(0)
    total_offset_end = timedelta(0)
    previous_nonuid_time_end = timedelta(0)
    if save_original_audio:
        merge_a_list = []
        a_total_length = timedelta(0)
    # Ищем все элементы ChapterAtom
    for chapter_atom in root.findall(".//ChapterAtom"):
        # Ищем ChapterSegmentUID, если он существует
        chapter_uid = chapter_atom.find("ChapterSegmentUID")
        chapter_uid_text = chapter_uid.text if chapter_uid is not None else None
        #если проверяем существование внешнего файла в chapters и uid не None возвращаем True
        if check_exist_ext_file and chapter_uid_text is not None: return True

        # Извлекаем ChapterTimeStart и ChapterTimeEnd
        time_start = str_to_timedelta(chapter_atom.find("ChapterTimeStart").text)
        time_end = str_to_timedelta(chapter_atom.find("ChapterTimeEnd").text)
        """
        # Выводим результаты
        print(f"DEBUG UID: {chapter_uid_text}")
        print(f"DEBUG Start Time: {time_start}")
        print(f"DEBUG End Time: {time_end}")
        print(f"DEBUG count: {count}")
        """
        if not check_exist_ext_file:
            if save_original_audio:
                needed_segment, previous_nonuid_time_end, total_length, total_offset_start, total_offset_end, a_needed_segment, a_total_length = get_linked_segment(directory, video_file, chapter_uid_text, time_start, time_end, previous_nonuid_time_end, count, total_length, total_offset_end, save_original_audio, a_total_length)
                merge_a_list.append(a_needed_segment.as_posix())
                #print(f"DEBUG merge_a_list: {merge_a_list}")
            else:
                needed_segment, previous_nonuid_time_end, total_length, total_offset_start, total_offset_end = get_linked_segment(directory, video_file, chapter_uid_text, time_start, time_end, previous_nonuid_time_end, count, total_length, total_offset_end)
            merge_list.append(needed_segment.as_posix())
            lengths_list.append(total_length)
            offsets_start_list.append(total_offset_start)
            #offsets_end_list.append(total_offset_end)
            count += 1
            #print(f"DEBUG merge_video_list: {merge_list} \nlengths_video_list {lengths_list}, \noffsets_start_list: {offsets_start_list}, \noffsets_end_list: {offsets_end_list}")
            #print("---\n---\n---")
    if save_original_audio:
        return merge_list, lengths_list, offsets_start_list, offsets_end_list, merge_a_list
    else:
        return merge_list, lengths_list, offsets_start_list, offsets_end_list

def merge_video_segments_radd_audiosubfont(output_file, merge_video_list, audio_list=None, subtitle_list=None, font_list=None):
    command = [mkvmerge.as_posix(), "-o", output_file.as_posix()]
    #добавляем видеофайлы
    command.append(merge_video_list[0])
    for video_file in merge_video_list[1:]:
        command.append(f"+{video_file}")
        #command.extend(["+", video_file])
    
    #Добавляем аудио, субтитры и шрифты если есть
    if audio_list is not None:
        command = command + audio_list
    if subtitle_list is not None:
        command = command + subtitle_list
    if font_list is not None:
        command = command + font_list

    try:
        print(f"Create merged video file by mkvmerge. Execute command: \n{command}")
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Error when execute command: {e}")
        sys.exit(1)
        
def format_font_list_txt(font_dir, font_list_txt):
    read_txt = read_lines_from_file(font_list_txt, 1)
    if read_txt:
        font_list = read_txt

    # Преобразование списка в строку
    font_list = ' '.join(font_list)

    # Удаление первых и последних символов, если это двойные кавычки
    if font_list.startswith('"') and font_list.endswith('"'):
        font_list = font_list[1:-1]

    formatted_font_list = []

    # Используем shlex.split для корректного разбивания строки
    for word in shlex.split(font_list):
        if word.startswith("--attach-file"):
            formatted_font_list.append(word)  # Добавляем флаг
        else:
            # Добавляем путь к файлу
            file_path = Path(font_dir) / word.strip('"')  # Убираем кавычки
            formatted_font_list.append(file_path.as_posix())  # Преобразуем в строку
            
    return formatted_font_list

def merge_audio_segments(save_directory, segments_list, count):
    output_file = Path(save_directory) / f"temp_audio_{count}.mka"
    command = [mkvmerge.as_posix(), "-o", output_file.as_posix()]
    command.append(segments_list[0])
    for segment in segments_list[1:]:
        command.append(f"+{segment}")
    try:
        #print(f"DEBUG Command: {' '.join(command)}")  # Для отладки
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Error when execute command: {e}")
    return output_file

def create_merge_audio_retimed_list(save_directory, input_file, lengths_video_list, offsets_start_list):
    count = 0
    start = timedelta(0)
    end = timedelta(0)
    previous_total_length = timedelta(0)
    a_total_length = timedelta(0)
    merge_audio_retimed_list = []
    for total_length in lengths_video_list:
        offset_start = offsets_start_list[count]
        offset_audio_to_video = a_total_length - previous_total_length
        segment_length = total_length - previous_total_length
        start_wo_offsets = total_length - segment_length
        start = start_wo_offsets - offset_start + offset_audio_to_video
        end = start + segment_length
        #print(f"DEBUG offset_start: {offset_start}, offset_audio_to_video: {offset_audio_to_video}, segment_length: {segment_length}, start_wo_offsets: {start_wo_offsets}, start: {start}, end: {end}")

        output_partname = set_split_partname(save_directory, count, start, ext="mka")
        a_needed_segment, a_segment_length, *_ = split_file(input_file, output_partname, start, end, a_total_length, None, file_type="audio", repeat_split=True)
        merge_audio_retimed_list.append(a_needed_segment.as_posix())
        a_total_length = a_total_length + a_segment_length
        previous_total_length = total_length
        count += 1
    return merge_audio_retimed_list

def create_audio_retimed_file(save_directory, input_file, count, lengths_video_list, offsets_start_list):
    merge_audio_retimed_list = create_merge_audio_retimed_list(save_directory, input_file, lengths_video_list, offsets_start_list)
    audio_retimed_file = merge_audio_segments(save_directory, merge_audio_retimed_list, count)
    return audio_retimed_file

def create_audio_retimed_list(save_directory, audio_file, lengths_video_list, offsets_start_list, merge_audio_list=None):
    count = 0
    audio_retimed_list = []
    if merge_audio_list is not None:
        audio_retimed_list.append(merge_audio_segments(save_directory, merge_audio_list, count).as_posix())
        count += 1
    if audio_file is not None:
        audio_retimed_list.append(create_audio_retimed_file(save_directory, audio_file, count, lengths_video_list, offsets_start_list).as_posix())
        count += 1
    #print(f"DEBUG return audio_retimed_list: {audio_retimed_list}")
    return audio_retimed_list

def adjust_subtitle_timing(filename, segment_start, segment_end, offset_start, remove_length):
    extended_start = segment_start - offset_start if segment_start > (segment_start - offset_start) else segment_start
    remove_border = segment_start + remove_length
    #print(f"DEBUG segment_start: {segment_start}, extended_start: {extended_start}, remove_border: {remove_border}, segment_end: {segment_end}")

    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(filename, 'w', encoding='utf-8') as file:
        for line in lines:
            # Ищем строки, начинающиеся с "Dialogue:"
            if line.startswith("Dialogue:"):
                # Извлекаем временные метки
                parts = line.split(',')
                str_dialogue_time_start = parts[1].strip()
                str_dialogue_time_end = parts[2].strip()
                #print(f"DEBUG \nstr_dialogue_time_start {str_dialogue_time_start} \nstr_dialogue_time_end {str_dialogue_time_end}")
                # Преобразуем временные метки в timedelta
                dialogue_time_start = str_to_timedelta(str_dialogue_time_start)
                dialogue_time_end = str_to_timedelta(str_dialogue_time_end)
                #print(f"DEBUG \ndialogue_time_start {dialogue_time_start} \ndialogue_time_end {dialogue_time_end}")

                #не включаем строки не входящие в сегмент
                if segment_start < dialogue_time_start < remove_border and segment_start < dialogue_time_end < remove_border:
                    #print(f"DEBUG remove line: {line}")
                    continue

                #регулируем внутри сегмента
                if extended_start < dialogue_time_end < segment_end:
                    # Применяем офсет
                    new_dialogue_time_start = dialogue_time_start + offset_start
                    new_dialogue_time_end = dialogue_time_end + offset_start
                    #преобразуем тайминги в строки
                    str_new_dialogue_time_start = timedelta_to_str(new_dialogue_time_start)
                    str_new_dialogue_time_end = timedelta_to_str(new_dialogue_time_end)
                    #print(f"DEBUG \nstr_new_dialogue_time_start {str_new_dialogue_time_start} \nstr_new_dialogue_time_end {str_new_dialogue_time_end}")
                    # Заменяем старые временные метки на новые
                    line = f"{parts[0]},{str_new_dialogue_time_start},{str_new_dialogue_time_end},{','.join(parts[3:])}"
                    #print(line)
            # Записываем строку в файл
            file.write(line)

def create_subtitle_retimed_file(save_directory, input_subtitle_file, name_count, lengths_video_list, offsets_start_list, offsets_end_list):
    subtitle_retimed_file = Path(save_directory) / f"temp_subtitle_{name_count}.ass"
    shutil.copy(input_subtitle_file, subtitle_retimed_file)
    count = 0
    previous_total_length = timedelta(0)
    for total_length in lengths_video_list:
        start = previous_total_length
        end = total_length
        offset_start = offsets_start_list[count]
        remove_length = previous_offset_start - offset_start if count > 0 else timedelta(0)
        if abs(offset_start) < timedelta(milliseconds=10) and abs(remove_length) < timedelta(milliseconds=10):
            previous_total_length = total_length
            previous_offset_start = offset_start
            count += 1
            continue
        #print(f"DEBUG offset_start: {offset_start}, remove_length: {remove_length}")
        adjust_subtitle_timing(subtitle_retimed_file, start, end, offset_start, remove_length)

        previous_total_length = total_length
        previous_offset_start = offset_start
        count += 1
    return subtitle_retimed_file

def create_subtitle_retimed_list(save_directory, input_subtitle_list, lengths_video_list, offsets_start_list, offsets_end_list):
    count = 0
    subtitle_retimed_list = []
    for subtitle in input_subtitle_list:
        subtitle_retimed_list.append(create_subtitle_retimed_file(save_directory, subtitle, count, lengths_video_list, offsets_start_list, offsets_end_list).as_posix())
        count += 1
    #print(f"DEBUG return subtitle_retimed_list: {subtitle_retimed_list}")
    return subtitle_retimed_list

def main():
    if len(sys.argv) < 8 or len(sys.argv) > 11:
        print("Usage: script.py <mkvinfo> <mkvmerge> <output_file> <directory> <video_file> <chapters_file> <audio_file> <subtitle_file> <font_dir> <font_list_txt>")
        sys.exit(1)

    global mkvinfo, mkvmerge
    mkvinfo = Path(sys.argv[1])
    mkvmerge = Path(sys.argv[2])
    output_file = Path(sys.argv[3])
    directory = Path(sys.argv[4])
    video_file = Path(sys.argv[5])
    chapters_file = Path(sys.argv[6])
    audio_file = Path(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7] else None
    subtitle_file = Path(sys.argv[8]) if len(sys.argv) > 8 and sys.argv[8] else None
    font_dir = Path(sys.argv[9]) if len(sys.argv) > 9 and sys.argv[9] else None
    font_list_txt = Path(sys.argv[10]) if len(sys.argv) > 10 and sys.argv[10] else None
    font_list = format_font_list_txt(font_dir, font_list_txt) if font_list_txt is not None else None
    """
    print(f"mkvinfo: {mkvinfo}\nmkvmerge: {mkvmerge}")
    print(f"output_file: {output_file}")
    print(f"Video file: {video_file}")
    print(f"Video dir: {directory}")
    print(f"Chapters file: {chapters_file}")
    print(f"Audio file: {audio_file}")
    print(f"Subtitle file: {subtitle_file}")
    print(f"font dir: {font_dir}")
    print(f"font list: {font_list}")
    """
    #если в chapters нет внешних файлов выходим
    check_exist_ext_file = True
    if not parse_chapters_file(chapters_file, directory, video_file, check_exist_ext_file):
        return None
    check_exist_ext_file = False

    save_original_audio = False
    if audio_file is None and subtitle_file is not None:
        save_original_audio = True

    parse_chapters_return = parse_chapters_file(chapters_file, directory, video_file, check_exist_ext_file, save_original_audio)
    if len(parse_chapters_return) == 5:
        merge_video_list, lengths_video_list, offsets_start_list, offsets_end_list, merge_audio_list = parse_chapters_return
    else:
        merge_video_list, lengths_video_list, offsets_start_list, offsets_end_list = parse_chapters_return
        merge_audio_list = None

    audio_retimed_list = None
    if audio_file is not None or merge_audio_list is not None:
        audio_retimed_list = create_audio_retimed_list(directory, audio_file, lengths_video_list, offsets_start_list, merge_audio_list)

    subtitle_retimed_list = None
    if subtitle_file is not None:
        subtitle_list = [subtitle_file.as_posix()]
        subtitle_retimed_list = create_subtitle_retimed_list(directory, subtitle_list, lengths_video_list, offsets_start_list, offsets_end_list)

    #завершаем
    merge_video_segments_radd_audiosubfont(output_file, merge_video_list, audio_retimed_list, subtitle_retimed_list, font_list)

if __name__ == "__main__":
    main()
