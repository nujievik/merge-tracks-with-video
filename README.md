# merge-tracks-with-video

## How to use

1. [Download](
https://github.com/nujievik/merge-tracks-with-video/releases) the
executable file (.exe) for Windows x64 or the packaged script set
(.pyz).
2. If you use the **script set**, install [dependencies](#dependencies).
3. Run it in the directory containing the videos or external tracks.

The default behavior can be changed by configuring the
[configuration file](
https://github.com/nujievik/merge-tracks-with-video/blob/main/config-merge-tracks-with-video.ini)
or by passing command-line arguments.
Usage `merge-tracks-with-video.exe --help` to print supported options.

## Dependencies

- [Chardet](https://github.com/chardet/chardet)
- [FFprobe](https://ffmpeg.org/download.html)
- [MKVToolNix](https://mkvtoolnix.download/)
- [Python](https://www.python.org/downloads/)
- [srt](https://github.com/cdown/srt)

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
3. Install:
```
pip install .
```
After installation, you can use the merge-tracks-with-video command in
your terminal or command prompt.
