import os

import options.manager

class _CommonParams():
    def set_opt(self, key, value, target):
        target, _, _ = self.replace_targets.get(target, (target, None, None))
        self.setted_opts.setdefault(target, set()).add(key)

        options.manager.set_opt(key, value, target)

    def get_opt(self, key, *args, **kwargs):
        if not args:
            if self.fpath in self.replace_targets:
                args = self.replace_targets[self.fpath][:2]
                args = (*args, os.path.dirname(args[0]))
            else:
                args = (self.fpath, self.fgroup, os.path.dirname(self.fpath))

        elif kwargs.pop('replace_targets', False):
            if args[0] in self.replace_targets:
                args = self.replace_targets[args[0]][:2]
                args = (*args, os.path.dirname(args[0]))

        if kwargs.get('pro_mode', None) is None:
            kwargs['pro_mode'] = self.pro_mode

        return options.manager.get_opt(key, *args, **kwargs)

    def set_common_params(self):
        self.setted_opts = {}
        self.replace_targets = {}
        self.append_to = {}
        get_opt = options.manager.get_opt
        self.pro_mode = get_opt('pro_mode')
        self.groups = {}
        for group in ['video', 'audio', 'signs', 'subtitles', 'fonts']:
            self.groups[group] = self.get_opt('files', group)
            setattr(self, f'{group}_list', [])
        self.track_groups = ['video', 'audio', 'signs', 'subtitles']

        self.save_dir = get_opt('save_directory')
        self.orig_attachs_dir = os.path.join(self.temp_dir, 'orig_attachs')
        self.orig_attachs_dir = self.files.ensure_end_sep(
            self.orig_attachs_dir)
        self.command_json = os.path.join(self.temp_dir, 'command.json')
        os.makedirs(self.temp_dir, exist_ok=True)

        self.verbose = get_opt('verbose')
        self.sorting_fonts = get_opt('sorting_fonts')
        self.locale_language = get_opt('locale_language')
        self.output = get_opt('output')
        self.count_gen = 0
        self.count_gen_earlier = 0

class Params(_CommonParams):
    def _clear_old_stem_info(self):
        self.append_to.clear()
        self.replace_targets.clear()
        for group in self.track_groups:
            getattr(self, f'{group}_list').clear()

        # Clear all except uids
        setted = self.files.info.setted
        uids = setted.pop('uids', {})
        uids.pop('', None)  # Remove nonuid info
        setted.clear()
        setted['uids'] = uids

        setted_opts = self.setted_opts
        for target in setted_opts:
            _dict = options.manager.setted.get(target, {})
            for key in setted_opts[target]:
                _dict.pop(key, None)
            if not _dict:  # Remove empty target
                options.manager.setted.pop(target, None)
        setted_opts.clear()

    def _set_file_lists(self):
        stem = self.stem
        for _dir, ftrie in self.files.dir_ftrie_pairs.items():
            if not self.get_opt('files', _dir):
                continue
            for f in ftrie.starts_with(stem):
                fpath = _dir + f
                if not self.get_opt('files', fpath):
                    continue

                fgroup = self.files.info.file_group(fpath)
                if self.groups[fgroup]:
                    lst = getattr(self, f'{fgroup}_list')
                    lst.append(fpath)

    def set_stem_params(self, stem):
        self.stem = stem
        self.files.info.stem = stem
        self._clear_old_stem_info()

        self._set_file_lists()
        if not self.video_list:
            return False

        self.base_video = self.video_list[0]
        self.fpath = self.base_video
        self.fgroup = 'video'

        for attr in [
            'need_retiming', 'extracted_orig', 'rm_linking',
            'rm_video_chapters', 'extracted_orig_fonts', 'new_chapters'
        ]:
            setattr(self, attr, False)

        return True

    def set_out_path(self, idx):
        if self.output:
            stem = self.idx_str.join(self.output)
        else:
            stem = self.stem

            if self.need_retiming:
                if self.retiming.need_cut:
                    stem += '_cutted_video'
                else:
                    stem += '_merged_video'

            for group in ['audio', 'subtitles']:
                if not getattr(self, f'{group}_list'):
                    continue

                if self.get_opt(f'{group}_tracks'):
                    stem += f'_added_{group}'
                else:
                    stem += f'_replaced_{group}'

        self.out_path = os.path.join(self.save_dir, f'{stem}.mkv')
        return True

"""
def init_fid_part_cmd(fid):
    if not fid:  # For fid 0
        params.command_parts = {}
    cmd = params.command_parts.setdefault(fid, {})['cmd'] = []
    params.command_parts[fid]['position_to_insert'] = 0
    return cmd

def init_fde_flags_params():
    params.counters_fde_flags = {}
    params.langs_default_audio = set()
    params.default_locale_audio = False
    params.setted_false_enabled_subtitles = False
"""
