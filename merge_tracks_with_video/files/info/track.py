import os

from merge_tracks_with_video.constants import PATTERNS

class Track():
    def _by_setted_opts_dict(self, _dict, fpath, opt_key, tid_init):
        for tid, val in _dict.items():
            _info = self.setted_info[fpath].setdefault(tid, {})
            _info[opt_key] = val
        return self.setted_info[fpath].get(tid_init, {}).get(opt_key, '')

    def track_name(self, tid, fpath, fgroup):
        _info = self.setted_info.setdefault(fpath, {}).setdefault(tid, {})

        if _info.get('name', None) is not None:
            return _info['name']

        _dir = os.path.dirname(fpath)
        name = self.get_opt('track_name', fpath, fgroup, _dir)
        if isinstance(name, dict):
            name = self._by_setted_opts_dict(name, fpath, 'name', tid)

        if not name:
            name = self.by_query('Name:', fpath, tid)

        if not name:
            name = self._clean_path_tail(fpath)
            if not len(name) > 2:
                name = self._clean_dir_name(fpath)

        _info['name'] = name
        return name

    def language(self, tid, fpath, fgroup):
        _info = self.setted_info.setdefault(fpath, {}).setdefault(tid, {})

        if _info.get('language', None) is not None:
            return _info['language']

        _dir = os.path.dirname(fpath)
        lang = self.get_opt('language', fpath, fgroup, _dir)
        if isinstance(lang, dict):
            lang = self._by_setted_opts_dict(lang, fpath, 'language', tid)

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
