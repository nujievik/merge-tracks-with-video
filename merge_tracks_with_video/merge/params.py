import os

from merge_tracks_with_video.options.manager import setted_opts

class _CommonParams():
    def execute(self, command, **kwargs):
        if kwargs.get('verbose', None) is None:
            kwargs['verbose'] = self.verbose
        return self.files.info.tools.execute(command, **kwargs)

    def set_opt(self, key, value, target):
        target, *_ = self.replace_targets.get(target, (target,))
        self.setted_opts.setdefault(target, set()).add(key)
        self.files.set_opt(key, value, target)

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

        return self.files.get_opt(key, *args, **kwargs)

    def set_common_params(self):
        self.setted_opts = {}
        self.replace_targets = {}
        self.append_to = {}

        get_opt = lambda x: self.get_opt(x, 'global', pro_mode=False)
        for attr in [
            'continue_on_error', 'locale_language', 'output', 'pro_mode',
            'sorting_fonts', 'verbose',
        ]:
            setattr(self, attr, get_opt(attr))

        self.groups = {}
        for group in ['video', 'audio', 'signs', 'subtitles', 'fonts']:
            self.groups[group] = self.get_opt('files', group)
            setattr(self, f'{group}_list', [])
        self.track_groups = ['video', 'audio', 'signs', 'subtitles']

        self.save_dir = get_opt('save_directory')
        self.orig_attachs_dir = self.files.ensure_end_sep(
            os.path.join(self.temp_dir, 'orig_attachs')
        )
        self.command_json = os.path.join(self.temp_dir, 'command.json')
        os.makedirs(self.temp_dir, exist_ok=True)

        self.count_gen = 0
        self.count_gen_earlier = 0

class Params(_CommonParams):
    def _clear_old_stem_info(self):
        self.append_to.clear()
        self.replace_targets.clear()
        for group in self.track_groups:
            getattr(self, f'{group}_list').clear()

        # Clear all except uids
        setted_info = self.files.info.setted_info
        uids = setted_info.pop('uids', {})
        uids.pop('', None)  # Remove nonuid info
        setted_info.clear()
        setted_info['uids'] = uids

        _setted_opts = self.setted_opts
        for target in _setted_opts:
            _dict = setted_opts.get(target, {})
            for key in _setted_opts[target]:
                _dict.pop(key, None)
            if not _dict:  # Remove empty target
                setted_opts.pop(target, None)
        _setted_opts.clear()

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

        self.chapters = None
        self.need_retiming = False

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
