# merge-tracks-with-video

The simple automated solution for merging video with external tracks.
The unique feature is the support for MKV segment linking.

## How to use

### Windows x64

1. [Download](
https://github.com/nujievik/merge-tracks-with-video/releases) the
executable file merge-tracks-with-video.exe
2. Run it in the directory containing the video or external tracks.

### Other system

1. Install dependencies:
    - [Python](https://www.python.org/downloads/)
    - Python modules
    ```
    pip install chardet
    ```
    ```
    pip install srt
    ```
    - [FFprobe (part of FFmpeg)](https://ffmpeg.org/download.html)
    - [MKVToolNix](https://mkvtoolnix.download/)
2. [Download](
https://github.com/nujievik/merge-tracks-with-video/releases) the
executable archive merge-tracks-with-video.pyz
3. Run it in the directory containing the video or external tracks.
```
python merge-tracks-with-video.pyz "file directory"
```

Alternatively, you can [install the package via pip](
#Installation-via-pip).

The default behavior can be changed by configuring the
[configuration file](
https://github.com/nujievik/merge-tracks-with-video/blob/main/config-merge-tracks-with-video.ini)
or by passing command-line arguments.
Usage `merge-tracks-with-video.exe --help` to print supported options.

## Notices

- Video and external tracks must have a same part of name. Example:
**Death Note - 01**.mkv and **Death Note - 01**.rus.aac
- Files will be searched in the start directory, in the base directory 
(topmost file directory relative start directory) and it's
subdirectories.

## Installation via pip

1. Clone the repository:
```
git clone https://github.com/nujievik/merge-tracks-with-video
```
2. Navigate to the repository directory:
```
cd merge-tracks-with-video
```
3. Install package:
```
pip install .
```
4. Install remainder dependencies:
    - [FFprobe (part of FFmpeg)](https://ffmpeg.org/download.html)
    - [MKVToolNix](https://mkvtoolnix.download/)

After installation, you can use the **merge-tracks-with-video** command
in your terminal or command prompt.
```
merge-tracks-with-video "file directory"
```

## Alternative GUI solutions

There are alternative solutions that offer a user-friendly GUI
interface, but they are less automated and do not support MKV segment
linking.

- [mkv-muxing-batch-gui](
https://github.com/yaser01/mkv-muxing-batch-gui). Advanced GUI.
- [py-mkvmergre-auto](https://github.com/LedyBacer/py-mkvmergre-auto).
Simple GUI
