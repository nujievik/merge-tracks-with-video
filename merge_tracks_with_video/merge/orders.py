class Orders():
    def _get_order_sort_key(self, fpath, fgroup, tids=[]):
        def get_opt(x):
            # Flag replace_targets=True will add parent dir to args
            return self.get_opt(
                x, fpath, fgroup, replace_targets=True, def_unset=False)

        if fpath in self.replace_targets:
            fpath, fgroup, _tid = self.replace_targets[fpath]
            tids = [_tid]

        _forced = get_opt('forced_display_flag')
        _default = get_opt('default_track_flag')
        _enabled = get_opt('track_enabled_flag')
        _flag_order = {True: 0, None: 1, False: 2}
        flag_sort = (_flag_order.get(_forced, 1),
                     _flag_order.get(_default, 1),
                     _flag_order.get(_enabled, 1))

        signs_sort = 0 if self.files.info.is_signs(fpath, tids) else 1

        langs = set()
        for tid in tids:
            langs.add(self.files.info.language(tid, fpath, fgroup))
        langs.discard('')  # Remove undefined
        if self.locale_language in langs:
            lang_sort = 0  # Locale first
        elif langs and not langs - {'jpn'}:
            lang_sort = 3  # Jpn latest
        elif langs:
            lang_sort = 2  # Other lang
        else:
            lang_sort = 1  # Undefined lang

        return (*flag_sort, signs_sort, lang_sort)

    def _set_file_orders(self):
        def get_sort_key(path):
            return self._get_order_sort_key(
                path, group, tids=self.files.info.file_tids(path))

        fids = {}
        fid = 0
        for group in self.groups['with_tracks']:
            lst = getattr(self, f'{group}_list')
            paths = sorted(lst) # sort by name
            sorted_paths = sorted(
                paths,
                key=get_sort_key
            )
            lst[:] = sorted_paths
            for path in lst:
                fids[path] = fid
                fid += 1
        return fids

    def _set_track_order(self, fids):
        fid_tid_group = {}
        fid_tid_pairs = []
        fid_tid_str = []

        def get_sort_key(item):
            return self._get_order_sort_key(*item)

        groups = self.groups
        replace_targets = self.replace_targets
        save_track = self.save_track
        tgroup_tids = self.files.info.tgroup_tids
        for group in groups['tracks']:
            args = []
            for _group in groups['with_tracks']:
                lst = getattr(self, f'{_group}_list')
                for path in lst:
                    # It's was extracted in self.retiming
                    if path in replace_targets and _group != 'video':
                        for tid in tgroup_tids(group, path):
                            args.append((path, _group, [tid]))
                    else:
                        _tracks = self.get_opt(f'{group}_tracks', path,
                                               _group, replace_targets=True)
                        for tid in tgroup_tids(group, path):
                            if save_track(tid, _tracks):
                                args.append((path, _group, [tid]))
            sorted_args = sorted(args, key=get_sort_key)
            for path, _, tids in sorted_args:
                fid = fids[path]
                tid = tids[0]  # tids always has 1 element
                fid_tid_group.setdefault(fid, {})[tid] = group
                fid_tid_pairs.append((fid, tid))
                fid_tid_str.append(f'{fid}:{tid}')

        order = self.track_order
        order.clear()
        order.update(fid_tid_group)
        order['fid_tid_pairs'] = fid_tid_pairs
        order['str'] = ','.join(fid_tid_str)

    def set_orders(self):
        fids = self._set_file_orders()
        self._set_track_order(fids)
