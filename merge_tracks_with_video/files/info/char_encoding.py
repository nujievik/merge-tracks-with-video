import os

import chardet

from constants import CHUNK_SIZE_READ, EXTS_SET

class CharEncoding():
    def char_encoding(self, fpath):
        _info = self.setted.setdefault(fpath, {})

        if _info.get('char_encoding', None) is not None:
            return _info['char_encoding']

        base, ext = os.path.splitext(fpath)

        if ext in EXTS_SET['matroska']:
            # All text in a Matroska(tm) file is encoded in UTF-8.
            # Source: (https://mkvtoolnix.download/doc/mkvmerge.html
            # #mkvmerge.text_files_and_charsets.introduction)
            encoding = 'utf-8'

        else:
            if (ext == '.sub' and
                os.path.exists(f'{base}.idx')
            ):
                fpath = f'{base}.idx'  # .idx stores encode info

            with open (fpath, 'rb') as f:
                data = f.read(CHUNK_SIZE_READ)

            encoding = chardet.detect(data)['encoding']

        _info['char_encoding'] = encoding
        return encoding
