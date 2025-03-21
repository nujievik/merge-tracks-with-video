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
        self.out_path = self.out_path.replace(
            '_merged_video', '_cutted_video')
        return True

    def processing_errors_and_warnings(self, stdout, msg):
        stdout_lines = stdout.splitlines()
        #last_line = stdout_lines[-1] if stdout_lines else ''
        verbose = self.verbose

        #Collect errors and warnings:
        errors = []
        warnings = []
        for line in stdout_lines:
            if line.startswith('Error:'):
                errors.append(line)
            elif line.startswith('Warning:'):
                warnings.append(line)

        # Print messages if need
        if verbose:
            print(stdout)
        elif verbose is None:
            for line in warnings:
                print(line)

        if not errors:
            print(msg)
            if any("The codec's private data does not match" in line
                   for line in warnings
            ):
                return self._processing_mismatched_codec_private_data()

        else:
            pass


"""
def mismatched_codec_params():
    if params.rm_linking:  # A linked parts was removed earlier
        return False

    print('Trying to generate another cutted version of the video '
          'without external video parts.')
    merge.retime.processing.codec_error()
    attachments.set_fonts_list()
    params.out_file = params.out_file.replace('_merged_', '_cutted_')

    return True

def chapters_not_recognized(last_line_out):
    if params.rm_video_chapters:
        return False

    print(f'{last_line_out}\nTrying to generate without chapters.')
    options.manager.set_target_option(params.base_video, 'chapters', False)
    params.rm_video_chapters = True

    return True

def file_not_recognized(last_line_out):
    fpath = last_line_out.split("'")[1]
    fpath = path_methods.path_to_normpath(fpath)

    if any(x == fpath for x in params.video_list):
        print(f'{last_line_out}\nUnrecognized video file! '
              'Skip generate for this video.')
        return False

    print(f'{last_line_out}\nTrying to generate without this file.')

    params.audio_list = [x for x in params.audio_list
                         if x != fpath]
    params.subtitles_list = [x for x in params.subtitles_list
                             if x != fpath]
    return True

def error_handling(command_out, lmsg):
    cleaned_out = ''.join(command_out.split()).lower()
    last_line_out = command_out.splitlines()[-1] if command_out else ''
    cleaned_lline_out = ''.join(last_line_out.split()).lower()

    if 'warning:' in cleaned_out:
        for line in command_out.splitlines():
            if line.lower().startswith('warning:'):
                print(line)

    if not cleaned_lline_out.startswith('error:'):
        print(lmsg)

        if "thecodec'sprivatedatadoesnotmatch" in cleaned_out:
            return mismatched_codec_params()

    elif 'containschapterswhoseformatwasnotrecognized' in cleaned_lline_out:
        return chapters_not_recognized(last_line_out)

    elif all(x in cleaned_lline_out
             for x in ('thetypeoffile', 'couldnotberecognized')):
        return file_not_recognized(last_line_out)

    else:
        if os.path.exists(params.out_file):
            os.remove(params.out_file)
        print(f'Error executing the command!\n{last_line_out}')
        executor.remove_temp_files()
"""
