import os
import re
import shutil

from merge_tracks_with_video.constants import EXTS

class _Extract():
    def _extract_attachs(self, source):
        names = []
        for line in self.files.info.stdout_mkvmerge_i(source):
            match = re.search(r"file name '(.+?)'", line)
            if match:
                name = match.group(1)
                names.append(name)
        if not names:
            return

        command = ['mkvextract', source, 'attachments']
        orig_attachs_dir = self.orig_attachs_dir
        sep = os.sep
        for idx, name in enumerate(names, start=1):
            command.append(f'{idx}:{orig_attachs_dir}{sep}{name}')

        self.execute(command, get_stdout=False, to_json=self.command_json)
        self.set_opt('fonts', False, source)

    def _set_extracted_fonts(self):
        orig_attachs_dir = self.orig_attachs_dir
        if os.path.exists(orig_attachs_dir):
            shutil.rmtree(orig_attachs_dir)

        def save_fonts():
            return self.get_opt('fonts', fpath, fgroup, replace_targets=True)
        _extract_attachs = self._extract_attachs
        exts = EXTS['matroska']
        replace_targets = self.replace_targets
        for fgroup in self.groups['with_tracks']:
            lst = getattr(self, f'{fgroup}_list')
            for fpath in lst:
                if fgroup == 'video' and self.need_retiming:
                    if not self.fonts:
                        continue
                    sources = {x for idx, x in self.retiming.sources.items()
                               if idx in self.retiming.indexes}
                    for source in sources:
                        _extract_attachs(source)
                else:
                    if not save_fonts():
                        continue
                    source, *_ = replace_targets.get(fpath, fpath)
                    if not os.path.splitext(source)[1] in exts:
                        continue
                    _extract_attachs(source)

        if not os.path.isdir(orig_attachs_dir):
            return

        extracted_fonts = self.extracted_fonts
        exts = EXTS['fonts']
        for f in os.listdir(orig_attachs_dir):
            if os.path.splitext(f)[1] in exts:
                extracted_fonts.add(f)

class Attachs(_Extract):
    def set_external_fonts(self):
        self.external_fonts = {}
        if not self.groups['fonts']:
            return

        dirs = self.dirs
        external_fonts = self.external_fonts
        get_opt = self.files.get_opt
        sep = os.sep
        for _dir, fonts in self.files.iterate_dir_fonts():
            if not dirs[_dir]:
                continue
            for f in fonts:
                if not get_opt('files', _dir + sep + f):
                    continue
                external_fonts[f] = _dir

    def set_fonts_list(self):
        self.extracted_fonts.clear()
        if self.sorting_fonts:
            self._set_extracted_fonts()

        if self.extracted_fonts:
            fonts_list = self.fonts_list
            fonts_list.clear()
            external_fonts = self.external_fonts
            extracted_fonts = self.extracted_fonts
            orig_attachs_dir = self.orig_attachs_dir
            names = extracted_fonts.union(set(external_fonts.keys()))
            sep = os.sep
            for name in sorted(names, key=str.lower):
                if name in external_fonts:
                    fonts_list.append(external_fonts[name] + sep + name)
                else:
                    fonts_list.append(orig_attachs_dir + sep + name)

        elif len(self.fonts_list) != len(self.external_fonts):
            fonts_list = self.fonts_list
            fonts_list.clear()
            external_fonts = self.external_fonts
            sep = os.sep
            for name in sorted(external_fonts.keys(), key=str.lower):
                fonts_list.append(external_fonts[name] + sep + name)
