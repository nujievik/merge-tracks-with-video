import sys

import files.find
import merge.params
import options.manager
import merge.processing
import third_party_tools
import options.set_methods
from version import __version__

def initial_options_and_tools():
    options.set_methods.set_initial_options()

    if options.manager.is_option_set('version'):
        print(f'merge-tracks-with-video v{__version__}')
        sys.exit(0)

    third_party_tools.set_tools_paths()

    if options.manager.get_option('rm_chapters'):
        third_party_tools.check_installation('ffmpeg')

def get_message(key):
    start_dir = options.manager.get_option('start_dir')
    save_dir = options.manager.get_option('save_dir')

    if key == 'try_gen':
        return ("Trying to generate a new video in the save directory "
                f"'{save_dir}' using files from the start directory "
                f"'{start_dir}'.")

    elif key == 'not_found':
        if options.manager.get_option('search_dirs'):
            limit = options.manager.get_option('lim_search_up')
            tail = f' and {limit} directories up.'
        else:
            tail = '.'

        return ("Files for generating a new video not found. Checked "
                f"the directory '{start_dir}' and its subdirectories{tail}")

    elif key == 'gen_earlier':
        return (f"{merge.params.count_gen_earlier} video files in the save "
                f"directory '{save_dir}' had generated names before the "
                "current run of the script. Generation for these files has "
                "been skipped.")

    elif key == 'gen_success':
        return ("\nThe generate was executed successfully. "
                f"{merge.params.count_gen} video files were generated in "
                f"the directory '{save_dir}'.")

def main():
    initial_options_and_tools()
    files.find.all_files_and_dirs()

    print(get_message('try_gen'))
    merge.processing.merge_all_files()

    if merge.params.count_gen_earlier:
        print(get_message('gen_earlier'))

    if merge.params.count_gen:
        print(get_message('gen_success'))
    else:
        print(get_message('not_found'))

if __name__ == '__main__':
    main()
