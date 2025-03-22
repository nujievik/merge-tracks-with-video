from merge_tracks_with_video.constants import (
    DEFAULT_OPTS,
    INVERSE_UNSET_ON_PRO
)

setted_opts = {}

def set_opt(key, value, target='global'):
    if not key in DEFAULT_OPTS['global']:
        # Debug check
        print(f"Warning: option '{key}' not in DEFAULT_OPTS['global']")
    setted_opts.setdefault(target, {})[key] = value

def get_opt(key, *args, **kwargs):
    def get_value():
        for target in args:
            value = setted_opts.get(target, {}).get(key, None)
            if value is not None:
                return value

        if kwargs.get('glob_unset', True):
            value = setted_opts.get('global', {}).get(key, None)

        if value is None and kwargs.get('def_unset', True):
            value = DEFAULT_OPTS['global'].get(key, None)
            if kwargs.get('pro_mode', False) and key in INVERSE_UNSET_ON_PRO:
                value = not value

        return value

    if not key in DEFAULT_OPTS['global']:
        # Debug check
        print(f"Warning: option '{key}' not in DEFAULT_OPTS['global']")
    if not args:
        args = ('global',)

    return get_value()
