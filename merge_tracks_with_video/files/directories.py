import os
import re

class Directories():
    def set_base_dir(self):
        limit_search_above = self.get_opt('limit_search_above')
        if not limit_search_above:
            # Set self.start_dir to self.base_dir
            self.base_dir = self.start_dir
            return

        start_dir = self.start_dir
        start_files = self.get_files_trie(start_dir)
        # Save start_files
        self.dir_ftrie_pairs[start_dir] = start_files
        limit_check_files = self.get_opt('limit_check_files')
        iterator = self.iterate_stems_with_tracks

        # Set start_dir to self.base_dir on starts_with(stem) > 1
        cnt = 1
        for stem in iterator(start_dir):
            if len(start_files.starts_with(stem)) > 1:
                self.base_dir = start_dir
                return
            cnt += 1
            if cnt > limit_check_files:
                break

        # Set above _dir to self.base_dir on starts_with(stem)
        _dir = start_dir
        for _ in range(limit_search_above):
            _dir = os.path.dirname(_dir)
            if not _dir:
                break

            cnt = 1
            for stem in iterator(_dir):
                if start_files.starts_with(stem):
                    self.base_dir = _dir
                    # self.base_dir above start_dir so set priority to
                    # files in start_dir
                    self.set_opt('track_enabled_flag', True, start_dir)
                    return
                cnt += 1
                if cnt > limit_check_files:
                    break

        # Set start_dir to self.base_dir if not found above
        self.base_dir = start_dir

    def _scan_dir_subdirs(self, path):
        len_base_dir = self.len_base_dir
        skip_directory_patterns = self.skip_directory_patterns
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_symlink() or not entry.is_dir():
                    continue
                _path = entry.path
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
        get_files_trie = self.get_files_trie

        if self.base_dir != self.start_dir:
            dir_ftrie_pairs[self.base_dir] = get_files_trie(self.base_dir)

        for _dir in self._iterate_subdirs(self.base_dir):
            if _dir in dir_ftrie_pairs:
                continue
            dir_ftrie_pairs[_dir] = get_files_trie(_dir)
