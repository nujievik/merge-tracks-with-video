/*
use merger::files::FileExtensions;
use merger::files::Files;
use std::collections::HashSet;

fn extensions_contains_exts(extensions: &HashSet<String>, exts: &[&str], group: &str) {
    for ext in exts.iter() {
        assert!(
            extensions.contains(*ext) || extensions.contains(ext.to_uppercase().as_str()),
            "Extension '{ext}' not found in '{group}' extensions"
        );
    }
}

#[test]
fn file_extensions_contains_exts() {
    let file_extensions = FileExtensions::new();

    let container = [
        "3gp", "av1", "avi", "f4v", "flv", "m2ts", "mkv", "mp4", "mpg", "mov", "mpeg", "ogg",
        "ogm", "ogv", "ts", "webm", "wmv",
    ];
    let audio = [
        "aac", "ac3", "caf", "dts", "dtshd", "eac3", "ec3", "flac", "m4a", "mka", "mlp", "mp2",
        "mp3", "mpa", "opus", "ra", "thd", "truehd", "tta", "wav", "weba", "webma", "wma",
    ];
    extensions_contains_exts(&file_extensions.audio, &container, "audio");
    extensions_contains_exts(&file_extensions.audio, &audio, "audio");

    let fonts = ["otf", "ttf"];
    extensions_contains_exts(&file_extensions.fonts, &fonts, "fonts");

    let matroska = ["mka", "mks", "mkv", "webm"];
    extensions_contains_exts(&file_extensions.matroska, &matroska, "matroska");

    let retiming_subtitles = ["ass", "srt"];
    extensions_contains_exts(
        &file_extensions.retiming_subtitles,
        &retiming_subtitles,
        "retiming_subtitles",
    );

    let subtitles = ["ass", "mks", "srt", "ssa", "sub", "sup"];
    extensions_contains_exts(&file_extensions.subtitles, &subtitles, "subtitles");

    let video = [
        "264", "265", "avc", "h264", "h265", "hevc", "ivf", "m2v", "mpv", "obu", "vc1", "x264",
        "x265", "m4v",
    ];
    extensions_contains_exts(&file_extensions.video, &container, "video");
    extensions_contains_exts(&file_extensions.video, &video, "video");

    extensions_contains_exts(&file_extensions.with_tracks, &audio, "with_tracks");
    extensions_contains_exts(&file_extensions.with_tracks, &subtitles, "with_tracks");
    extensions_contains_exts(&file_extensions.with_tracks, &video, "with_tracks");
}
*/
