import os
import sys

from merge_tracks_with_video.constants import EXTS_TUPLE

class Errors():
    def _processing_mismatched_codec_private_data(self):
        # A linked segments was removed earlier
        if not self.get_opt('linked_segments'):
            return False

        if not self.verbose is False:
            print('Trying to generate another cutted version of the video '
                  'without linked segments.')

        self.retiming.processing_mismatched_codec_private_data()
        self.set_fonts_list()
        if not self.output:  # Auto name
            self.out_path = self.out_path.replace(
                '_merged_video', '_cutted_video')
        return True

    def _get_fpath_from_error(self, error):
        splits = error.split("'")
        fpath = ''
        for idx, s in enumerate(splits):
            if s.endswith(EXTS_TUPLE['total']):
                fpath = "'".join(splits[1:idx+1])
        return fpath

    def _processing_chapters_format_not_recognized(self, error):
        fpath = self._get_fpath_from_error(error)
        if self.get_opt('chapters', fpath):
            print('Trying to generate without chapters.')
            self.set_opt('chapters', False, fpath)
            return True

    def _processing_file_not_recognized(self, error):
        fpath = self._get_fpath_from_error(error)
        for fgroup in self.groups['total']:
            lst = getattr(self, f'{fgroup}_list')
            for idx, _fpath in enumerate(lst):
                if _fpath == fpath:
                    lst[:] = lst[:idx] + lst[idx+1:]
                    if self.video_list:
                        if not lst and not self.output:
                            self.out_path = self.out_path.replace(
                                f'_added_{fgroup}', '')
                            self.out_path = self.out_path.replace(
                                f'_replaced_{fgroup}', '')

                        print(f'Trying to generate without the file {fpath}.')
                        return True

                    else:
                        print('Error: Unrecognized video file.')
                        return False

    def processing_errors_and_warnings(self, stdout, msg):
        stdout_lines = stdout.splitlines()
        verbose = self.verbose

        # Collect warnings and error
        warnings = []
        for line in stdout_lines:
            if line.startswith('Warning:'):
                warnings.append(line)
        error = ''
        if stdout_lines:
            _last_line = stdout_lines[-1]
            if _last_line.startswith('Error:'):
                error = _last_line

        # Print messages if need
        if verbose:
            print(stdout)
        elif verbose is None:
            for line in warnings:
                print(line)

        if not error:
            print(msg)
            if any("The codec's private data does not match" in x
                   for x in warnings
            ):
                return self._processing_mismatched_codec_private_data()

        else:
            if verbose is None:
                print(error)

            if 'contains chapters whose format was not recognized.' in error:
                val = self._processing_chapters_format_not_recognized(error)

            elif all(x in error for x in [
                'The type of file', 'could not be recognized.']
            ):
                val = self._processing_file_not_recognized(error)
            else:
                val = False

            if val:
                return True  # Trying generate again
            else:
                print('Error executing the merge command.')
                if os.path.exists(self.out_path):
                    os.remove(self.out_path)

                if self.continue_on_error:
                    print('Trying to generate next files.')
                else:
                    if verbose is None:
                        print(stdout)
                    sys.exit(1)
