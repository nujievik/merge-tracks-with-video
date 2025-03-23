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

        return self.files.get_opt(key, *args, **kwargs)

    def set_common_params(self):
        self.append_to = {}
        self.groups = {}
        self.replace_targets = {}
        self.setted_opts = {}
        self.track_order = {}

        pro_mode = self.get_opt('pro_mode', 'global')
        def get_opt(x):
            return self.get_opt(x, 'global', pro_mode=pro_mode)
        attrs = [
            'adding_default_track_flags', 'adding_forced_display_flags',
            'adding_languages', 'adding_sub_charsets',
            'adding_track_enabled_flags', 'adding_track_names',
            'adding_track_orders', 'continue_on_error', 'locale_language',
            'output', 'sorting_fonts', 'verbose',
        ]
        for x in attrs:
            setattr(self, x, get_opt(x))
        if any(getattr(self, x) for x in attrs[:6]):
            self.need_adding = True
        else:
            self.need_adding = False

        groups = self.groups
        groups['total'] = ['video', 'audio', 'signs', 'subtitles', 'fonts']
        for group in groups['total']:
            groups[group] = self.get_opt('files', group)
            setattr(self, f'{group}_list', [])
        groups['with_tracks'] = groups['total'][:-1]
        groups['tracks'] = ['video', 'audio', 'subtitles']

        self.save_dir = get_opt('save_directory')
        self.orig_attachs_dir = self.files.ensure_end_sep(
            os.path.join(self.temp_dir, 'orig_attachs')
        )
        self.command_json = os.path.join(self.temp_dir, 'command.json')
        os.makedirs(self.temp_dir, exist_ok=True)

        self.count_gen = 0
        self.count_gen_earlier = 0

class Params(_CommonParams):
    def _clear_setted_on_previos_stem(self):
        self.append_to.clear()
        self.replace_targets.clear()
        for group in self.groups['with_tracks']:
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
        self._clear_setted_on_previos_stem()

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
