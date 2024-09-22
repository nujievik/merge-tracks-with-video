"""
merge-video-from-split-chapters-v0.3.1
This program is part of the generate-video-with-these-files-script repository
Licensed under GPL-3.0. See LICENSE file for details.
Author: nujievik Email: nujievik@gmail.com
"""
import sys
import xml.etree.ElementTree as ET
import os
import subprocess
import re
import shlex
from pathlib import Path

def is_zero_time_format(value):
    # Регулярное выражение для проверки формата
    pattern = r'^(0+(:0+){2}(\.\d+)?|0+)$'
    if re.match(pattern, value):
        return True
    return False

def get_file_uid(filepath):
    try:
        result = subprocess.run(["mkvinfo", filepath], capture_output=True, text=True, check=True)
        output = result.stdout

        # Ищем UID в выводе
        for line in output.splitlines():
            if "UID" in line:
                uid_hex = line.split(":")[-1].strip()
                # Преобразуем в строку формата 93828424aeb8a27a942fb070d17459f8
                uid_clean = "".join(byte[2:] for byte in uid_hex.split() if byte.startswith("0x"))
                return uid_clean
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении mkvinfo для файла {filepath}: {e}")

    return None
    
def write_lines_to_file(filename, *args):
    # Записываем переменные в файл
    with open(filename, 'w', encoding='utf-8') as file:
        for line in args:
            file.write(f"{line}\n")

    print(f"Data written to the file {filename}")
    
def read_lines_from_file(filename, num_lines):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Проверяем, что в файле достаточно строк
        if len(lines) >= num_lines:
            return [line.strip() for line in lines[:num_lines]]
        else:
            return None

    except FileNotFoundError:
        error_message = f"Файл '{filename}' не найден.\n"
        # Печатаем с использованием системного буфера
        sys.stdout.buffer.write(error_message.encode('utf-8'))
        return None

def find_video_file_with_uid(directory, target_uid):
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(".mkv"):
            filepath = os.path.join(directory, filename)
            file_uid = get_file_uid(filepath)
            print(f"fileuid: {file_uid}")
            if file_uid.lower() == target_uid.lower(): #сравниваем uid в одном регистре
                return filepath

    return None
    
    
def split_video(input_video, output_partname, chapter_time_start, chapter_time_end):
    command = [
        "mkvmerge", "-o", output_partname,
        "--split", f"timecodes:{chapter_time_start},{chapter_time_end}",
        "--no-chapters", input_video
    ]
    print(f"DEBUG command {command}")
    # Выполняем команду
    subprocess.run(command)
    
def parse_chapters_file(chapters_file, video_dir, video_file, check_exist_ext_file=False):
    start_split_video = False
    #если не проверяем существование внешнего файла в chapters (уже знаем что он существует) ставим флаг сплитования
    if not check_exist_ext_file:
        start_split_video = True
    
    # Парсим XML-файл
    tree = ET.parse(chapters_file)
    root = tree.getroot()

    count = 0
    merge_video_list = []
    # Ищем все элементы ChapterAtom
    for chapter_atom in root.findall(".//ChapterAtom"):     
        count += 1
        # Ищем ChapterSegmentUID, если он существует
        chapter_segment_uid = chapter_atom.find("ChapterSegmentUID")
        chapter_segment_uid_text = chapter_segment_uid.text if chapter_segment_uid is not None and len(chapter_segment_uid.text) > 3 else None
        #если проверяем существование внешнего файла в chapters и uid не None возвращаем True
        if check_exist_ext_file and chapter_segment_uid_text is not None: return True

        # Извлекаем ChapterTimeStart и ChapterTimeEnd
        chapter_time_start = chapter_atom.find("ChapterTimeStart").text
        chapter_time_end = chapter_atom.find("ChapterTimeEnd").text

        # Выводим результаты
        print(f"DEBUG UID: {chapter_segment_uid_text}")
        print(f"DEBUG Start Time: {chapter_time_start}")
        print(f"DEBUG End Time: {chapter_time_end}")
        print(f"DEBUG count: {count}")

        
        # устанавливаем начало имени сплитов
        split_partname = f"temp_{count}.mkv"
        
        # какой индекс у нужного сплита
        if is_zero_time_format(chapter_time_start) is True:
            temp_file_index = "-001"
        else:
            temp_file_index = "-002"
        # предполагаемое имя нужного сплита
        temp_split_name = Path (video_dir) / f"temp_{count}{temp_file_index}.mkv"
        
        if not check_exist_ext_file:
            start_split_video = True
        # если uid пуст сплитуем текущее видео
        if chapter_segment_uid_text is None:
            print("UID is missing")
            video_to_be_split = video_file
            #переназначаем начало сплита и записываем конец сплита в переменную - сделано потому что mkvmerge переходит при сплите к следующему ключевому кадру от указанного времени
            try:
                previous_chapter_end
            except NameError:
                previous_chapter_end = chapter_time_end
            else:
                chapter_time_start = previous_chapter_end
                previous_chapter_end = chapter_time_end
        else:
            print(f"UID: {chapter_segment_uid_text}")
            # Пробуем считать данные из txt
            temp_uid_split_txt = Path(video_dir) / f"temp_{chapter_segment_uid_text}.txt"
            print(f"temp text file: {temp_uid_split_txt}")
            read = read_lines_from_file(temp_uid_split_txt, 3)
            if read:
                line1, line2, line3 = read
                print(line1)
                print(line2)
                print(line3)
                video_to_be_split = line1
                #если время предыдущего сплита совпадает
                if line2 == chapter_time_start and line3 == chapter_time_end:
                    print(f"DEBUG line2 and chapterstart and lin3 and chapterend equal")
                    #и нужный сплит существует не сплитуем
                    temp_split_name = Path (video_dir) / f"temp_{chapter_segment_uid_text}.mkv"
                    if temp_split_name.exists():
                        print(f"DEBUG set dont split flag")
                        start_split_video = False
       
            else:
                print(f"DEBUG read temtxt failure")
                video_to_be_split = find_video_file_with_uid(video_dir, chapter_segment_uid_text)
                write_lines_to_file(temp_uid_split_txt, video_to_be_split, chapter_time_start, chapter_time_end)
            
        print(f"DEBUG split video: {video_to_be_split}")
        
        # сплитуем если нужно
        if start_split_video:
            print(f"DEBUG start split video.")
            split_video(video_to_be_split, split_partname, chapter_time_start, chapter_time_end)
            #имя нужного сплита
            temp_split_name = Path (video_dir) / f"temp_{count}{temp_file_index}.mkv"
            print(f"DEBUG temp split name: {temp_split_name}")
            # если сплит по внешнему файлу переименовываем его чтоб использовать дальше
            if chapter_segment_uid_text is not None:
                new_split_name = Path (video_dir) / f"temp_{chapter_segment_uid_text}.mkv"
                print(f"chapter segment uid is not None. new split name: {new_split_name}")
                #если файл уже есть удаляем
                if os.path.exists(new_split_name): 
                    os.remove(new_split_name)
                os.rename(temp_split_name, new_split_name)
                temp_split_name = new_split_name
        
        # формируем merge video list
        merge_video_list.append(temp_split_name.as_posix())
        
        print(f"DEBUG temp split name: {temp_split_name}")
        print(f"DEBUG merge_video_list: {merge_video_list}")
        print("---")
    
    return merge_video_list

def merge_splits(mkvmerge, output_file, merge_video_list, audio_file=None, subtitle_file=None, font_dir=None, font_list=None):
     # Начинаем команду с mkvmerge и опции -o
    command = [mkvmerge.as_posix(), "-o", output_file.as_posix()]
    if merge_video_list:
        command.append(merge_video_list[0])  # Первый файл без +

        # Добавляем остальные файлы с пробелом перед +
        for video_file in merge_video_list[1:]:
            command.append("+")
            command.append(video_file)  # Добавляем с пробелом
    
    #Добавляем аудио, субтитры и шрифты если есть
    if audio_file is not None:
        command.append(audio_file.as_posix())
    if subtitle_file is not None:
        command.append(subtitle_file.as_posix())
    if font_list is not None:
        command = command + font_list

    try:
        print(f"DEBUG Command: {' '.join(command)}")  # Для отладки
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")
        
def format_font_list_txt(font_dir, font_list_txt):
    read_txt = read_lines_from_file(font_list_txt, 1)
    if read_txt:
        font_list = read_txt

    print(font_list)

    # Преобразование списка в строку
    font_list = ' '.join(font_list)

    print(font_list)

    # Удаление первых и последних символов, если это двойные кавычки
    if font_list.startswith('"') and font_list.endswith('"'):
        font_list = font_list[1:-1]
    
    print(font_list)

    command = []

    # Используем shlex.split для корректного разбивания строки
    for word in shlex.split(font_list):
        if word.startswith("--attach-file"):
            command.append(word)  # Добавляем флаг
        else:
            # Добавляем путь к файлу
            file_path = font_dir / word.strip('"')  # Убираем кавычки
            command.append(str(file_path))  # Преобразуем в строку
            
    print(command)
    return command

    print(command)

def main():
    if len(sys.argv) < 8 or len(sys.argv) > 11:
        print("Usage: script.py <mkvinfo> <mkvmerge> <output_file> <video_dir> <video_file> <chapters_file> <audio_file> <subtitle_file> <font_dir> <font_list_txt>")
        sys.exit(1)

    mkvinfo = Path(sys.argv[1])
    mkvmerge = Path(sys.argv[2])
    output_file = Path(sys.argv[3])
    video_dir = Path(sys.argv[4])
    video_file = Path(sys.argv[5])
    chapters_file = Path(sys.argv[6])
    audio_file = Path(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7] else None
    subtitle_file = Path(sys.argv[8]) if len(sys.argv) > 8 and sys.argv[8] else None
    font_dir = Path(sys.argv[9]) if len(sys.argv) > 9 and sys.argv[9] else None
    font_list_txt = Path(sys.argv[10]) if len(sys.argv) > 10 and sys.argv[10] else None
    font_list = format_font_list_txt(font_dir, font_list_txt) if font_list_txt is not None else None

    # Пример вывода полученных файлов
    print(f"mkvinfo: {mkvinfo}")
    print(f"mkvmerge: {mkvmerge}")
    print(f"outout: {output_file}")
    print(f"Video file: {video_file}")
    print(f"Video dir: {video_dir}")
    print(f"Chapters file: {chapters_file}")
    print(f"Audio file: {audio_file}")
    print(f"Subtitle file: {subtitle_file}")
    print(f"font dir: {font_dir}")
    print(f"font list: {font_list}")
    
    if not parse_chapters_file(chapters_file, video_dir, video_file, True):
        return None
    merge_video_list = parse_chapters_file(chapters_file, video_dir, video_file)
    merge_splits(mkvmerge, output_file, merge_video_list, audio_file, subtitle_file, font_dir, font_list)
  
if __name__ == "__main__":
    main()