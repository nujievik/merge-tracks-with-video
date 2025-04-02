# merge-tracks-with-video

A simple automated solution for merging video with external tracks. The
unique feature is the support for MKV segment linking.

## How to use

1. [Download](
https://github.com/nujievik/merge-tracks-with-video/releases) the
executable file (.exe) for Windows x64 or the executable archive
(.pyz) for other system.
2. If you use the **executable archive**, install [dependencies](
#dependencies).
3. Run it in the directory containing the video or external tracks.

The default behavior can be changed by configuring the
[configuration file](
https://github.com/nujievik/merge-tracks-with-video/blob/main/config-merge-tracks-with-video.ini)
or by passing command-line arguments.
Usage `merge-tracks-with-video.exe --help` to print supported options.

## Dependencies

- [Python](https://www.python.org/downloads/)
- Python modules:
    - [Chardet](https://github.com/chardet/chardet)
    - [srt](https://github.com/cdown/srt)
- [FFprobe](https://ffmpeg.org/download.html)
- [MKVToolNix](https://mkvtoolnix.download/)

## Notices

- Video and external tracks must has a same part of name. Example:
**Death Note - 01**.mkv and **Death Note - 01**.rus.aac
- Files will be searched in the start directory, in the base directory 
(topmost file directory) and it's subdirectories.

## Installation via pip

Alternatively, you can install the package via pip:
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
    - [FFprobe](https://ffmpeg.org/download.html)
    - [MKVToolNix](https://mkvtoolnix.download/)

After installation, you can use the **merge-tracks-with-video** command
in your terminal or command prompt.

## Alternative GUI solutions

There are alternative solutions that offer a user-friendly GUI
interface, but they are less automated and do not support MKV segment
linking.

- [mkv-muxing-batch-gui](
https://github.com/yaser01/mkv-muxing-batch-gui). Advanced GUI.
- [py-mkvmergre-auto](https://github.com/LedyBacer/py-mkvmergre-auto).
Simple GUI
