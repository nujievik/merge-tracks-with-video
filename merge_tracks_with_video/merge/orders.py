class Orders():
    def _get_order_sort_key(self, fpath, fgroup, tids=[]):
        if fpath in self.replace_targets:
            fpath, fgroup, _tid = self.replace_targets[fpath]
            tids = [_tid]
        # replace_targets=True will add parent dir to args
        get_opt = lambda x: self.get_opt(
            x, fpath, fgroup, replace_targets=True, def_unset=False)

        _forced = get_opt('forced_display_flag')
        _default = get_opt('default_track_flag')
        _enabled = get_opt('track_enabled_flag')
        _flag_order = {True: 0, None: 1, False: 2}
        flag_sort = (_flag_order.get(_forced, 1),
                     _flag_order.get(_default, 1),
                     _flag_order.get(_enabled, 1))

        langs = set()
        for tid in tids:
            lang = self.files.info.language(tid, fpath, fgroup)
            if lang:
                langs.add(lang)
        if self.locale_language in langs:
            lang_sort = 0  # Locale first
        elif langs and not langs - {'jpn'}:
            lang_sort = 3  # Jpn latest
        elif langs:
            lang_sort = 2  # Other lang
        else:
            lang_sort = 1  # Undefined lang

        return (*flag_sort, lang_sort)

    def _set_file_orders(self):
        fids = {}
        fid = 0
        for group in self.track_groups:
            lst = getattr(self, f'{group}_list')
            paths = sorted(lst) # sort by name
            sorted_paths = sorted(
                paths,
                key=lambda path: self._get_order_sort_key(
                    path,
                    group,
                    tids=self.files.info.file_tids(path)
                )
            )
            lst[:] = sorted_paths
            for path in lst:
                fids[path] = fid
                fid += 1
        return fids

    def _set_track_order(self, fids):
        order = []
        order_str = []
        track_groups = self.track_groups
        for group in track_groups:
            args = []
            for _group in track_groups:
                lst = getattr(self, f'{_group}_list')
                for path in lst:
                    for tid in self.files.info.tgroup_tids(group, path):
                        args.append((path, _group, [tid]))
            sorted_args = sorted(
                args, key=lambda item: self._get_order_sort_key(*item)
            )
            for path, _, tids in sorted_args:
                fid = fids[path]
                tid = tids[0]  # tids always has 1 element
                order.append((fid, tid))
                order_str.append(f'{fid}:{tid}')
        self.track_order = order
        self.track_order_str = ','.join(order_str)

    def set_orders(self):
        fids = self._set_file_orders()
        self._set_track_order(fids)
