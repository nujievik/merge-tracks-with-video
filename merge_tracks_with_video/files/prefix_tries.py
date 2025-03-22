import os

from merge_tracks_with_video.constants import EXTS_TUPLE

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

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

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

    def delete(self, word):
        self._delete(self.root, word, 0)

    def _delete(self, node, word, index):
        if index == len(word):
            if node.is_end_of_word:
                node.is_end_of_word = False
            return self._should_delete_node(node)

        char = word[index]
        if char not in node.children:
            return False

        child_node = node.children[char]
        should_delete_child = self._delete(child_node, word, index + 1)

        if should_delete_child:
            del node.children[char]

        return not node.is_end_of_word and not node.children

    def _should_delete_node(self, node):
        return not node.is_end_of_word and not node.children

class PrefixTries():
    def get_stems_trie(self, path):
        trie = Trie()
        for stem in self._iterate_dir_stems(path):
            trie.insert(stem)
        return trie

    def get_files_trie(self, path):
        trie = Trie()
        for f in self._iterate_dir_files(path):
            trie.insert(f)
        return trie

    def _iterate_dir_stems(self, path):
        skip_file_patterns = self.skip_file_patterns
        with os.scandir(path) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                name = entry.name
                if not name.endswith(EXTS_TUPLE['total_wo_fonts']):
                    continue

                if not any(key in name for key in skip_file_patterns):
                    yield name.rsplit('.', 1)[0]

    def _iterate_dir_files(self, path):
        skip_file_patterns = self.skip_file_patterns
        with os.scandir(path) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                name = entry.name
                if not name.endswith(EXTS_TUPLE['total_wo_fonts']):
                    continue

                if not any(key in name for key in skip_file_patterns):
                    yield name
