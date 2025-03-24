import os
import re
import shutil

from merge_tracks_with_video.constants import EXTS

class _Extract():
    def _get_attach_names(self, fpath):
        names = []
        for line in self.files.info.stdout_mkvmerge_i(fpath):
            match = re.search(r"file name '(.+?)'", line)
            if match:
                name = match.group(1)
                names.append(name)
        return names

    def _extract_attachs(self):
        if os.path.exists(self.orig_attachs_dir):
            shutil.rmtree(self.orig_attachs_dir)

        for fpath in self.video_list + self.signs_list + self.subtitles_list:
            if not os.path.splitext(fpath)[1] in EXTS['matroska']:
                continue
            names = self._get_attach_names(fpath)
            if not names:
                continue

            command = ['mkvextract', fpath, 'attachments']
            for _idx, name in enumerate(names, start=1):
                font = os.path.join(self.orig_attachs_dir, name)
                command.append(f'{_idx}:{font}')

            self.execute(command, get_stdout=False)
            self.set_opt('fonts', False, fpath)

    def _set_extracted_fonts(self):
        _dir = self.orig_attachs_dir
        if not os.path.isdir(_dir):
            return

        extracted_fonts = self.extracted_fonts
        for f in os.listdir(_dir):
            if os.path.splitext(f)[1] in EXTS['fonts']:
                extracted_fonts.add(f)

class Attachs(_Extract):
    def _set_ext_fonts(self):
        if getattr(self, 'ext_fonts', None) is None:
            self.ext_fonts = {}
            for _dir, fonts in self.files.iterate_dir_fonts():
                if not self.get_opt('files', _dir):
                    continue
                for f in fonts:
                    if not self.get_opt('files', _dir + f):
                        continue
                    self.ext_fonts[f] = _dir

    def _set_fonts_list_if_extracted(self):
        orig_attachs_dir = self.orig_attachs_dir
        extracted_fonts = self.extracted_fonts
        ext_fonts = self.ext_fonts
        fonts_list = []
        if self.groups['fonts']:
            names = extracted_fonts.union(set(ext_fonts.keys()))
            for name in sorted(names, key=str.lower):
                if name in ext_fonts:
                    fonts_list.append(ext_fonts[name] + name)
                else:
                    fonts_list.append(orig_attachs_dir + name)
        self.fonts_list = fonts_list

    def _set_fonts_list_if_len_mismatch(self):
        ext_fonts = self.ext_fonts
        fonts_list = []
        if self.groups['fonts']:
            for name in sorted(ext_fonts.keys(), key=str.lower):
                fonts_list.append(ext_fonts[name] + name)
        self.fonts_list = fonts_list

    def set_fonts_list(self):
        self.extracted_fonts = set()
        self._set_ext_fonts()
        if self.sorting_fonts:
            self._extract_attachs()
            self._set_extracted_fonts()

        if self.extracted_fonts:
            self._set_fonts_list_if_extracted()
        elif len(self.fonts_list) != len(self.ext_fonts):
            self._set_fonts_list_if_len_mismatch()
