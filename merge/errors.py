import os
import re

import executor
import path_methods
import options.manager
import splitted.processing
import file_info.by_mkvtools
from . import attachments, command_maker, params

def mismatched_codec_params():
    if params.rm_linking:  # A linked parts was removed earlier
        return False

    print('Trying to generate another cutted version of the video '
          'without external video parts.')
    splitted.processing.processing_codec_error()
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
