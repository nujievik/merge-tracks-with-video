import os
import re

class _BaseDir():
    def ensure_end_sep(self, path):
        return path + self.sep if path[-1] != self.sep else path

    def delete_stems_doubles(self):
        stems = self.stems
        to_delete = set()
        for stem in stems.starts_with(''):
            _stems = stems.starts_with(stem)
            if len(_stems) > 1:
                for _stem in _stems:
                    if _stem != stem:
                        to_delete.add(_stem)
        for stem in to_delete:
            stems.delete(stem)

    def find_base_dir(self):
        base_dir = None
        stems = self.get_stems_trie(self.start_dir)
        files = self.get_files_trie(self.start_dir)
        self.dir_ftrie_pairs[self.start_dir] = files

        for stem in stems.starts_with(''):
            if len(files.starts_with(stem)) > 1:
                self.stems = stems
                self.base_dir = self.start_dir
                return

        _dir = os.path.dirname(self.start_dir)
        for _ in range(self.get_opt('limit_search_above')):
            _dir = os.path.dirname(_dir)
            if not _dir:
                break
            _stems = self.get_stems_trie(_dir)
            for _stem in _stems.starts_with(''):
                if stems.starts_with(_stem):
                    to_delete = set()
                    for _stem in _stems.starts_with(''):
                        if not stems.starts_with(_stem):
                            to_delete.add(_stem)
                    for stem in to_delete:
                        _stems.delete(stem)

                    self.stems = _stems
                    self.base_dir = self.ensure_end_sep(_dir)
                    # Set priority for files in start_directory
                    start_dir = os.path.normpath(self.start_dir)
                    self.set_opt('track_enabled_flag', True, start_dir)
                    return

        self.stems = stems
        self.base_dir = self.start_dir

class Directories(_BaseDir):
    def _scan_dir_subdirs(self, path):
        sep = self.sep
        len_base_dir = self.len_base_dir
        skip_directory_patterns = self.skip_directory_patterns

        with os.scandir(path) as entries:
            for entry in entries:
                if not entry.is_dir():
                    continue
                _path = entry.path + sep
                _rel_path = _path[len_base_dir:].lower()
                words = set(re.findall(r'\b\w+\b', _rel_path))
                if not words & skip_directory_patterns:
                    yield _path

    def _iterate_subdirs(self, path):
        for _dir in self._scan_dir_subdirs(path):
            yield _dir
            yield from self._iterate_subdirs(_dir)

    def set_dir_ftrie_pairs(self):
        dir_ftrie_pairs = self.dir_ftrie_pairs
        if self.base_dir != self.start_dir:
            files = self.get_files_trie(self.base_dir)
            dir_ftrie_pairs[self.base_dir] = files

        for _dir in self._iterate_subdirs(self.base_dir):
            if _dir in dir_ftrie_pairs:
                continue
            dir_ftrie_pairs[_dir] = self.get_files_trie(_dir)
