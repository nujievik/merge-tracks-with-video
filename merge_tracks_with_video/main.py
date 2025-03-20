import os
import shutil
import uuid

import files.make_instance
import merge.make_instance
import options.settings
import tools

def _get_message(key):
    start_dir = options.manager.get_opt('start_dir')
    save_dir = options.manager.get_opt('save_dir')

    if key == 'try_gen':
        return ("Trying to generate a new video in the save directory "
                f"'{save_dir}' using files from the start directory "
                f"'{start_dir}'.")

    elif key == 'not_found':
        if options.manager.get_opt('search_dirs'):
            limit = options.manager.get_opt('lim_search_up')
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
    tools.init()
    options.settings.init()
    files_instance = files.make_instance.init()

    save_dir = files_instance.get_opt('save_directory')
    temp_dir = os.path.join(
        save_dir, f'__temp_files__.{str(uuid.uuid4())[:8]}')
    try:
        merge = init(files_instance, temp_dir)
        merge.processing()
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    main()
