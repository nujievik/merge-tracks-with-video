# merge-tracks-with-video

## Script for fast merging external tracks with video

## How to use

1. [Download](
https://github.com/nujievik/merge-tracks-with-video/releases) the
executable file (.exe) for Windows x64 or the packaged script set
(.pyz).
2. If you use the **script set**, install [dependencies](#dependencies).
3. Run it in the directory containing the videos or external tracks.

The default behavior can be changed by configuring the
[configuration file](#configuration-file) or by passing
[command-line arguments](#command-line-arguments). In particular, you
don't need to copy the script into the directory with the files, but
you can simply pass the directory as an argument:

```
merge-tracks-with-video.exe "directory with files"
```

## Dependencies

- [Chardet](https://github.com/chardet/chardet)
- [FFprobe](https://ffmpeg.org/download.html)
- [MKVToolNix](https://mkvtoolnix.download/)
- [Python](https://www.python.org/downloads/)
- [srt](https://github.com/cdown/srt)

## License

- **Own Code**: [GNU General Public License v3.0](
https://www.gnu.org/licenses/gpl-3.0.html)
- **Chardet**: [GNU Lesser General Public License v2.1](
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **FFprobe** (part of FFmpeg):
[GNU Lesser General Public License v2.1](
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **MKVToolNix**: [GNU General Public License v2.0](
https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
- **Python**: [PSF License](https://www.python.org/psf/license/)
- **srt**: [MIT License](https://opensource.org/license/MIT)
