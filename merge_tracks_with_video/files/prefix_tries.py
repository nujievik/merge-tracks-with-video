import os

from merge_tracks_with_video.constants import EXTS, EXTS_LENGTHS

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        words = []
        self._find_words(node, prefix, words)
        return words

    def _find_words(self, node, prefix, words):
        if node.is_end_of_word:
            words.append(prefix)
        for char, child in node.children.items():
            self._find_words(child, prefix + char, words)

class PrefixTries():
    def get_stems_trie(self, path):
        trie = Trie()
        for stem in self.iterate_stems_with_tracks(path):
            trie.insert(stem)
        return trie

    def get_files_trie(self, path):
        trie = Trie()
        for f in self.iterate_files_with_tracks(path):
            trie.insert(f)
        return trie

    def iterate_stems_with_tracks(self, path):
        exts = EXTS['with_tracks']
        lengths = EXTS_LENGTHS['with_tracks']
        skip_file_patterns = self.skip_file_patterns
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_symlink() or not entry.is_file():
                    continue
                name = entry.name
                for length in lengths:
                    if not name[-length:] in exts:
                        continue
                    skip = False
                    for key in skip_file_patterns:
                        if key in name:
                            skip = True
                            break
                    if not skip:
                        yield name.rsplit('.', 1)[0]
                        break

    def iterate_files_with_tracks(self, path):
        exts = EXTS['with_tracks']
        lengths = EXTS_LENGTHS['with_tracks']
        skip_file_patterns = self.skip_file_patterns
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_symlink() or not entry.is_file():
                    continue
                name = entry.name
                for length in lengths:
                    if not name[-length:] in exts:
                        continue
                    skip = False
                    for key in skip_file_patterns:
                        if key in name:
                            skip = True
                            break
                    if not skip:
                        yield name
                        break
