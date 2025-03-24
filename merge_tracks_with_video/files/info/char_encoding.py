import os

import chardet

from merge_tracks_with_video.constants import CHUNK_SIZE_READ, EXTS

class CharEncoding():
    def char_encoding(self, fpath):
        _info = self.setted_info.setdefault(fpath, {})

        if _info.get('char_encoding', None) is not None:
            return _info['char_encoding']

        base, ext = os.path.splitext(fpath)

        if ext in EXTS['matroska']:
            # All text in a Matroska(tm) file is encoded in UTF-8.
            # Source: (https://mkvtoolnix.download/doc/mkvmerge.html
            # #mkvmerge.text_files_and_charsets.introduction)
            encoding = 'utf-8'

        else:
            if (ext.lower() == '.sub' and
                os.path.exists(f'{base}{ext}')
            ):
                fpath = f'{base}{ext}'  # .idx stores encode info

            with open (fpath, 'rb') as f:
                data = f.read(CHUNK_SIZE_READ)

            encoding = chardet.detect(data)['encoding']

        _info['char_encoding'] = encoding
        return encoding
