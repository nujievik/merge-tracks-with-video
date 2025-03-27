import os

import chardet

from merge_tracks_with_video.constants import (
    ACCEPTABLE_ENCODING_CONFIDENCE,
    CHUNK_SIZE_READ,
    EXTS
)

class CharEncoding():
    def char_encoding(self, fpath):
        _info = self.setted_info.setdefault(fpath, {})

        if _info.get('char_encoding', None) is not None:
            return _info['char_encoding']

        if os.path.splitext(fpath)[1] in EXTS['matroska']:
            # All text in a Matroska(tm) file is encoded in UTF-8.
            # Source: (https://mkvtoolnix.download/doc/mkvmerge.html
            # #mkvmerge.text_files_and_charsets.introduction)
            encoding = 'utf-8'

        else:
            with open (fpath, 'rb') as f:
                data = f.read(CHUNK_SIZE_READ)

            _detect = chardet.detect(data)
            if _detect['confidence'] >= ACCEPTABLE_ENCODING_CONFIDENCE:
                encoding = _detect['encoding']
            else:
                encoding = 'utf-8'

        _info['char_encoding'] = encoding
        return encoding
