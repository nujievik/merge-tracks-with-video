from .flags import flags

def flag(key, value, check_exists=False):
    if not check_exists or key in flags:
        flags[key] = value
    else:
        print(f"Error flag '{key}' not found, flag not set.")

def for_flag(key2, key3, value):
    if key3 == 'options':
        value = flags.get('for', {}).get(key2, {}).get('options', []) + value
    flags.setdefault('for', {}).setdefault(key2, {})[key3] = value
