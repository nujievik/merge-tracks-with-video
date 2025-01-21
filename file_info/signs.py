from pathlib import Path

from files.files import KEYS
from files.find_ext import path_has_keyword

def is_signs(base_video, filepath, tname):
    if path_has_keyword(Path(''), Path(tname), KEYS['signs']):
        return True

    if path_has_keyword(base_video, filepath, KEYS['signs']):
        return True
