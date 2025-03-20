import os

from constants import PATTERNS
import options.manager

class _TrackName():
    def _tname_by_path(self, fpath):
        tail = self._clean_path_tail(fpath)
        if len(tail) > 2:
            return tail
        else:
            return self._clean_dir_name(fpath)

    def track_name(self, tid, fpath, fgroup):
        _info = self.setted.setdefault(fpath, {}).setdefault(tid, {})

        if _info.get('name', None) is not None:
            return _info['name']

        _dir = os.path.dirname(fpath)
        name = options.manager.get_opt('track_name', fpath, fgroup, _dir)
        if not name:
            name = self.by_query('Name:', fpath, tid)
        if not name:
            name = self._tname_by_path(fpath)

        _info['name'] = name
        return name

class Track(_TrackName):
    def language(self, tid, fpath, fgroup):
        _info = self.setted.setdefault(fpath, {}).setdefault(tid, {})

        if _info.get('language', None) is not None:
            return _info['language']

        lang = options.manager.get_opt('language', fpath, fgroup)
        if not lang:
            lang = self.by_query('Language', fpath, tid)

        if not lang or lang not in PATTERNS['languages']:
            tname = self.track_name(tid, fpath, fgroup)
            for _lang, keys in PATTERNS['languages'].items():
                if (lang in keys or
                    self.path_has_key(fpath, keys) or
                    self.path_has_key(tname, keys)
                    ):
                    lang = _lang
                    break

        _info['language'] = lang
        return lang
