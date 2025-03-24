import os
import re

from merge_tracks_with_video.constants import EXTS_LOWER

class PathOps():
    def _relative_path(self, path):
        return path[self.len_base_dir:]

    def _relative_dir(self, path):
        rel_path = self._relative_path(path)
        if os.path.isfile(path):
            return os.path.dirname(rel_path)
        else:
            return rel_path

    def _dir_name(self, path):
        rel_dir = self._relative_dir(path)
        return os.path.basename(rel_dir)

    def _clean_dir_name(self, path):
        name = self._dir_name(path)

        if (name.startswith('[') and
            name.endswith(']') and
            name.count('[') == 1
            ):
            name = name.strip(' _.[]')
        else:
            name = name.strip(' _.')

        return name

    def _path_tail(self, path):
        name = os.path.basename(path)
        stem = name.rsplit('.', 1)[0]
        return stem.replace(self.stem, '')

    def _clean_path_tail(self, path):
        tail = self._path_tail(path)

        while True:
            new_tail = re.sub(r'\.[a-zA-Z0-9]{1,3}\.', '', tail)
            if new_tail != tail:
                tail = new_tail
            else:
                break

        for ext in EXTS_LOWER['total']:
            if tail.lower().startswith(ext):
                tail = tail[len(ext):]
            if tail.lower().endswith(ext):
                tail = tail[:-len(ext)]

        tail = tail.strip(' _.')
        if (tail.startswith('[') and
            tail.endswith(']') and
            tail.count('[') == 1
            ):
            tail = tail.strip('[]')

        return tail

    def path_has_key(self, path, keys):
        rel_dir = self._relative_dir(path)
        tail = self._path_tail(path)

        search_str = f'{rel_dir}/{tail}'.lower()
        words = set(re.findall(r'\b\w+\b', search_str))

        return True if words & keys else False
