import locale

from files.files import KEYS
from . import set_flag

def set_locale():
    for element in locale.getlocale():
        locale_words = set(element.split('_'))
        for lang, keys in KEYS['lang'].items():
            if keys & locale_words:
                set_flag.flag('locale', lang)
                return
