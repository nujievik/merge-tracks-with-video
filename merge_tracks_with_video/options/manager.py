from constants import DEFAULT_OPTS, INVERSE_UNSET_ON_PRO

setted = {}

def set_opt(key, value, target='global'):
    if not key in DEFAULT_OPTS['global']:
        # Debug check
        print(f"Warning: option '{key}' not in DEFAULT_OPTS['global']")
    setted.setdefault(target, {})[key] = value

def get_opt(key, *args, **kwargs):
    if not key in DEFAULT_OPTS['global']:
        # Debug check
        print(f"Warning: option '{key}' not in DEFAULT_OPTS['global']")
    if not args:
        args = ('global',)
    _get_opt = _GetOpt(key, args, kwargs)
    return _get_opt.value

class _GetOpt():
    def __init__(self, key, args, kwargs):
        self.key = key
        self.args = args
        self.kwargs = kwargs
        self.value = self._get_value()

    def _get_value(self):
        key = self.key
        value = None
        kwargs = self.kwargs

        for target in self.args:
            value = setted.get(target, {}).get(key, None)
            if value is not None:
                return value

        if kwargs.get('glob_unset', True):
            value = setted.get('global', {}).get(key, None)

        if value is None and kwargs.get('def_unset', True):
            value = DEFAULT_OPTS['global'].get(key, None)
            if kwargs.get('pro_mode', False) and key in INVERSE_UNSET_ON_PRO:
                value = not value

        return value
