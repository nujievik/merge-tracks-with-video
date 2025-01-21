str_paths = {
    'ffprobe': '',
    'mkvextract': '',
    'mkvinfo': '',
    'mkvmerge': ''
}

PACKAGE = {
    'ffmpeg': {
        'ffprobe'
    },
}
PACKAGE['mkvtoolnix'] = set(str_paths.keys()) - PACKAGE['ffmpeg']
