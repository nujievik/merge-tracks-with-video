import files.find
import tools.set_paths
import tools.installed
from merge import merge
from version import __version__
from flags import get_flag, set_initial

def main():
    set_initial.set_initial_flags()

    if get_flag.flag('version'):
        print(f'generate-video-with-these-files v{__version__}')

    if not get_flag.flag('lim_gen'):
        print("A new video can't be generated because the limit-generate set to 0.")
        return

    tools.set_paths.set_tools_paths()

    if get_flag.flag('rm_chapters'):
        tools.installed.ffmpeg()

    print(f"Trying to generate a new video in the save directory '{str(get_flag.flag("save_dir"))}' "
          f"using files from the start directory '{str(get_flag.flag("start_dir"))}'.")

    lmsg = f"Files for generating a new video not found. Checked the directory '{str(get_flag.flag('start_dir'))}'"
    lmsg = f"{lmsg}, its subdirectories and {get_flag.flag("lim_search_up")} directories up."

    files.find.find_all_files()

    if not files.find.files['video']:
        print(lmsg)
        return
    elif get_flag.flag('range_gen')[0] > len(files.find.files['video']):
        print("A new video can't be generated because the start range-generate exceeds the number of video files.")
        return

    merge.merge_all_files()

    if merge.params.count_gen_before:
        print(f"{merge.params.count_gen_before} video files in the save directory '{str(get_flag.flag("save_dir"))}' "
              "had generated names before the current run of the script. Generation for these files has been skipped.")

    if merge.params.count_gen:
        print(f"\nThe generate was executed successfully. {merge.params.count_gen} video files were generated"
              f"in the directory '{str(get_flag.flag("save_dir"))}'")
    else:
        print(lmsg)

if __name__ == '__main__':
    main()
