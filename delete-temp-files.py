import os
import sys

def delete_temp_files(directory):
    try:
        # Получаем список всех файлов в указанной директории
        for filename in os.listdir(directory):
            # Проверяем, начинается ли имя файла на 'temp_'
            if filename.startswith("temp_"):
                file_path = os.path.join(directory, filename)
                # Удаляем файл
                os.remove(file_path)
                print(f"Deleted temp file: {file_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
    else:
        directory = sys.argv[1]
        delete_temp_files(directory)