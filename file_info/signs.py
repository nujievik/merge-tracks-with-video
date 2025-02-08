import path_methods
from files.constants import PATTERNS

def is_signs(fpath, base_video, tname):
    keys = PATTERNS['signs']
    if (path_methods.path_has_keyword(tname, '', keys) or
        path_methods.path_has_keyword(fpath, base_video, keys)
        ):
        return True
    else:
        return False
