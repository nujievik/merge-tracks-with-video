from .flags import DEFAULT, flags

def flag(key, default_if_missing=True):
    value = flags.get(key, None)
    if value is None and default_if_missing:
        value = DEFAULT.get(key, None)
    return value

def for_flag(key2, key3):
    return flags.get('for', {}).get(key2, {}).get(key3, None)
