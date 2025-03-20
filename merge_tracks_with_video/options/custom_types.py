import argparse
import os
import re

from constants import PATTERNS
from metadata import __package_name__
import tools

class CustomTypes():
    def __init__(self):
        self.mkvtoolnix_lang_codes = set()

    def _get_str_vals(self, raw):
        vals = raw.split(',')
        return [val.strip() for val in vals]

    def output(self, raw):
        vals = raw.split(',')
        return (vals[0], ''.join(vals[1:]))

    def remove_segments(self, raw):
        vals = self._get_str_vals(raw)
        return set(vals)

    def _check_readable(self, path):
        if not os.path.exists(path):
            raise argparse.ArgumentTypeError(
                f"directory '{path}' not exists.")

        elif not os.access(path, os.R_OK):
            raise argparse.ArgumentTypeError(
                    (f"you do not have permission to READ from "
                     f"directory '{path}'"))

    def _check_writable(self, path):
        _path = path
        while _path:
            if os.path.exists(_path):
                if os.access(_path, os.W_OK):
                    break

                raise argparse.ArgumentTypeError(
                    (f"you do not have permission to WRITE to "
                     f"directory '{path}'."))

            _path = os.path.dirname(_path)

    def _path_dir(self, raw, readable=False, writable=False):
        path = os.path.abspath(raw)
        if readable:
            self._check_readable(path)
        if writable:
            self._check_writable(path)
        return path

    def _to_int(self, raw):
        try:
            return int(raw)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"value '{raw}' is not a valid integer.")

    def start_directory(self, raw):
        return self._path_dir(raw, readable=True)

    def save_directory(self, raw):
        return self._path_dir(raw, writable=True)

    def _set_mkvtoolnix_lang_codes(self):
        if self.mkvtoolnix_lang_codes:
            return  # Earlier setted
        mkvtoolnix_lang_codes = self.mkvtoolnix_lang_codes

        command = ['mkvmerge', '--list-languages']
        stdout = tools.execute(command)
        pattern = re.compile(r"\|\s*([a-z]{2,3})\s*\|?")

        for line in stdout.splitlines()[2:]:
            matches = pattern.findall(line)
            mkvtoolnix_lang_codes.update(matches)

    def positive_int(self, raw):
        value = self._to_int(raw)
        if value <= 0:
            raise argparse.ArgumentTypeError(
                f"value '{raw}' is not a positive integer.")
        return value

    def non_negative_int(self, raw):
        value = self._to_int(raw)
        if value < 0:
            raise argparse.ArgumentTypeError(
                f"value '{raw}' is not a non-negative integer.")
        return value

    def range_generate(self, raw):
        str_vals = re.split(r'[-,]', raw)
        str_vals = [x for x in str_vals if x]
        if len(str_vals) not in {1, 2}:
            raise argparse.ArgumentTypeError(
                f"range '{raw}' is not a 1 or 2 numbers.")

        vals = []
        for val in str_vals:
            vals.append(self.non_negative_int(val))

        if len(vals) > 1 and vals[1] < vals[0]:
            raise argparse.ArgumentTypeError(
                f"end of range '{raw}' is not equal or greater than start.")
        elif len(vals) == 1:
            if raw.startswith(('-', ',')):
                vals[0:0] = [1]
            else:
                vals.append(9999999)

        return vals

    def language_code(self, raw):
        self._set_mkvtoolnix_lang_codes()

        lang = raw.strip()
        if not lang in self.mkvtoolnix_lang_codes:
            raise argparse.ArgumentTypeError(
                f"language code '{raw}' is not supported.\n"
                f"Usage: {__package_name__} --mkvmerge --list-languages to "
                f"print supported codes")
        else:
            for _lang, keys in PATTERNS['languages'].items():
                if lang in keys:
                    lang = _lang
                    break
            return lang

    def tracks(self, raw):
        vals = set()
        if raw.startswith(('-', '!')):
            raw = raw[1:]
            vals.add('!')

        str_vals = self._get_str_vals(raw)
        for val in str_vals:
            if re.match(r'^[0-9]+$', val):
                val = self.non_negative_int(val)
            else:
                val = self.language_code(val)
            vals.add(val)

        return vals

    def language(self, raw):
        str_vals = self._get_str_vals(raw)
        vals = {}
        for val in str_vals:
            if '0' <= val[:1] <= '9' and ':' in val:
                tid, lang = val.split(':', 1)
                tid = self.non_negative_int(tid)
                lang = self.language_code(lang)
                vals[tid] = lang
            elif len(str_vals) == 1:
                vals = self.language_code(val)
            else:
                raise argparse.ArgumentTypeError(
                    f"language values '{raw}' has not TID prefixes")
        return vals

    def track_name(self, raw):
        str_vals = self._get_str_vals(raw)
        vals = {}
        for val in str_vals:
            if '0' <= val[:1] <= '9' and ':' in val:
                tid, name = val.split(':', 1)
                tid = self.non_negative_int(tid)
                vals[tid] = name
            elif len(str_vals) == 1:
                vals = val
            else:
                raise argparse.ArgumentTypeError(
                    f"value '{raw}' is not TID:name[,TID:name] or single name")

        return vals

    def track_bool_flag(self, raw):
        vals = {}
        str_vals = self._get_str_vals(raw)

        for val in str_vals:
            if '0' <= val[:1] <= '9':
                if ':' in val:
                    tid, _val = val.split(':', 1)
                    _val = PATTERNS['bool'].get(_val.lower(), None)
                    if _val is not None:
                        tid = self.non_negative_int(tid)
                    else:
                        raise argparse.ArgumentTypeError(
                            (f"value '{raw}' is not TID[:bool][,TID[:bool]] "
                             "or single True/False")
                        )
                else:
                    tid = self.non_negative_int(val)
                    _val = True
                vals[tid] = _val

            elif len(str_vals) == 1 and val.lower() in PATTERNS['bool']:
                vals = PATTERNS['bool'][val.lower()]

            else:
                raise argparse.ArgumentTypeError(
                    (f"value '{raw}' is not TID[:bool][,TID[:bool]] "
                     "or single True/False")
                )
        return vals
