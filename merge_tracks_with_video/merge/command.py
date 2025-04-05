class Command():
    def _get_group_tracks_pcommand(self):
        if self.fpath in self.replace_targets and self.fgroup != 'video':
            return []  # It's was extracted in self.retiming

        part = []
        for _group in self.groups['tracks']:
            key = f'{_group}_tracks'
            value = self.get_opt(key)
            if value is False:
                part.append(f'--no-{_group}')
            elif isinstance(value, set):
                val = '!' if '!' in value else ''
                sorted_vals = sorted(str(x) for x in value - {'!'})
                val += ','.join(sorted_vals)
                _g = 'subtitle' if _group[0] == 's' else _group
                part.extend([f'--{_g}-tracks', val])
        return part

    def _get_file_pcommand(self, fpath, fgroup):
        part = []
        self.fpath = fpath
        self.fgroup = fgroup

        part.extend(self._get_group_tracks_pcommand())

        if not self.get_opt('fonts'):
            part.append('--no-attachments')
        if not self.get_opt('chapters'):
            part.append('--no-chapters')

        part.extend(self.get_opt('specials'))

        _part = part.copy()
        part.append(fpath)
        _append = [f'+{x}' for x in self.append_to.get(fpath, [])]
        for x in _append:
            part.extend(_part)
            part.append(x)

        return part

    def _add_track_opts_parts(self, parts):
        def _get_flag_value():
            value = get_opt(flag)
            if isinstance(value, dict):
                value = value.get(tid, None)
            limit = get_opt(f'limit_{flag}')
            tgroup = order[fid][tid]
            # Earlier signs tracks was saved as subtitles because
            # MKVToolnix don't separate it. Here need separate it
            if tgroup == 'subtitles' and is_signs(fpath, [tid]):
                tgroup = 'signs'
            count = flags.setdefault(tgroup, {}).setdefault(flag, 0)

            if count >= limit:
                val = 0
            # User settings
            elif value is not None:
                val = value
            # Auto settings
            elif (flag == 'default_track_flag' and
                  tgroup == 'subtitles' and
                  (flags.get('default_locale_audio', False) or
                   language in flags.get('langs_default_audio', set())
                   )
            ):
                val = 0
            else:
                val = 1

            if val:
                flags[tgroup][flag] += 1
                if tgroup == 'audio' and flag == 'default_track_flag':
                    langs = flags.setdefault('langs_default_audio', set())
                    langs.add(language)
                    if language == self.locale_language:
                        flags['default_locale_audio'] = True

            return '' if val else ':0'

        def get_opt(x):
            return self.get_opt(x, fpath, fgroup, replace_targets=True)

        flags = {}
        positions = {}
        info = self.files.info
        is_signs = self.files.info.is_signs
        order = self.track_order
        replace_targets = self.replace_targets

        for fid, tid in order['fid_tid_pairs']:
            part = []
            fpath, fgroup = parts['targets'][fid]
            if fpath in replace_targets:
                fpath, fgroup, _tid = replace_targets[fpath]
                retimed = True
            else:
                _tid = tid
                retimed = False

            if self.adding_track_names:
                track_name = info.track_name(_tid, fpath, fgroup)
                if track_name:
                    part.extend(['--track-name', f'{tid}:{track_name}'])

            if self.adding_languages:
                language = info.language(_tid, fpath, fgroup)
                if language:
                    part.extend(['--language', f'{tid}:{language}'])

            for flag in ['forced_display_flag', 'default_track_flag',
                         'track_enabled_flag']:
                if not getattr(self, f'adding_{flag}s'):
                    continue
                val = _get_flag_value()
                part.extend([f"--{flag.replace('_', '-')}", f'{tid}{val}'])

            # Retimed subtitles already in utf-8
            if not retimed and fgroup in {'signs', 'subtitles'}:
                encoding = info.char_encoding(fpath)
                if (encoding and  # These encodings are recognized auto
                    not encoding.lower().startswith(('utf-', 'ascii'))
                ):
                    part.extend(['--sub-charset', f'{tid}:{encoding}'])

            pos = positions.setdefault(fid, 0)
            parts[fid][pos:pos] = part
            positions[fid] += len(part)

        return parts

    def get_merge_command(self):
        command = ['mkvmerge', '-o', self.out_path]

        if isinstance(self.chapters, str):
            command.extend(['--chapters', self.chapters])
        if self.adding_track_orders:
            command.extend(['--track-order', self.track_order['str']])

        parts = {'targets': {}}
        fid = -1
        for fgroup in self.groups['with_tracks']:
            lst = getattr(self, f'{fgroup}_list')
            for fid, fpath in enumerate(lst, start=fid+1):
                parts[fid] = self._get_file_pcommand(fpath, fgroup)
                parts['targets'][fid] = (fpath, fgroup)

        if self.need_adding:
            parts = self._add_track_opts_parts(parts)

        for fid in range(fid+1):
            command.extend(parts[fid])

        specials = self.get_opt('specials', 'fonts', glob_unset=False)
        for font in self.fonts_list:
            command.extend(specials + ['--attach-file', font])

        return command
