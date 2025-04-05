import os
import shutil
import uuid

import merge_tracks_with_video.files.make_instance
import merge_tracks_with_video.merge.make_instance
import merge_tracks_with_video.options.settings
import merge_tracks_with_video.tools

def main():
    merge_tracks_with_video.tools.init()
    merge_tracks_with_video.options.settings.init()
    files_instance = merge_tracks_with_video.files.make_instance.init()

    get_opt = files_instance.get_opt
    start_dir = get_opt('start_directory')
    save_dir = get_opt('save_directory')
    verbose = not get_opt('verbose') is False  # True on unset and True

    if verbose:
        print(f"Trying to generate a merged video in the save directory "
              f"'{save_dir}' using files from the start directory "
              f"'{start_dir}'.")

    temp_dir = os.path.join(
        save_dir, f'temp_files.{str(uuid.uuid4())[:8]}')
    try:
        merge = merge_tracks_with_video.merge.make_instance.init(
            files_instance, temp_dir)
        merge.processing()
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    if not merge.count_gen:
        limit = get_opt('limit_search_above')
        above = '' if not limit else f', {limit} directories above,'
        print(f"Files for generating a new merged video not found. Checked "
              f"the directory '{start_dir}'{above} and its subdirectories.")
    elif verbose:
        print(f"\nThe generate was executed successfully. "
              f"{merge.count_gen} merged video were generated in the "
              f"directory '{save_dir}'.")

if __name__ == '__main__':
    main()
