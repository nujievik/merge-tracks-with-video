import re
from pathlib import Path

from .files import KEYS

def path_has_keyword(videopath, filepath, keywords):
    search_str = str(filepath.parent).replace(str(videopath.parent), '').lower()
    search_str = f"{search_str}/{filepath.stem.replace(videopath.stem, '').lower()}"
    words = set(re.findall(r'\b\w+\b', search_str))
    if keywords & words:
        return True

def find_ext_files(search_dir, extensions, search_name='', recursive=False):
    if not search_dir or not search_dir.exists():
        return []
    search_method = search_dir.rglob('*') if recursive else search_dir.glob('*')
    found_files = []

    for filepath in sorted(search_method):
        if recursive and path_has_keyword(search_dir, filepath.parent, KEYS['skip_dir']):
            continue

        elif any(key in filepath.stem for key in KEYS['skip_file']):
            continue

        elif (search_name in filepath.stem or filepath.stem in search_name) and filepath.is_file() and filepath.suffix.lower() in extensions:
            found_files.append(filepath)

    return found_files
