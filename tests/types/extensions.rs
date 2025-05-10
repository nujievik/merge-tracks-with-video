use mux_media::types::extensions::{AUDIO, FONTS, MATROSKA, RTM_SUBS, SUBS, TRACK_IN, VIDEO};
use std::collections::HashSet;
use std::ffi::OsStr;

fn case_permutations(s: &str) -> Vec<String> {
    fn helper(chars: &[char], current: String, result: &mut Vec<String>) {
        if chars.is_empty() {
            result.push(current);
        } else {
            let mut lower = current.clone();
            lower.push(chars[0].to_ascii_lowercase());
            helper(&chars[1..], lower, result);

            let mut upper = current;
            upper.push(chars[0].to_ascii_uppercase());
            helper(&chars[1..], upper, result);
        }
    }

    let mut result = Vec::new();
    helper(&s.chars().collect::<Vec<_>>(), String::new(), &mut result);
    result
}

fn assert_all_permutations_present(set: &HashSet<&OsStr>, ext: &str) {
    for case in case_permutations(ext) {
        assert!(
            set.contains(OsStr::new(&case)),
            "Set should contain variant: {}",
            case
        );
    }
}

fn assert_all_permutations_absent(set: &HashSet<&OsStr>, ext: &str) {
    for case in case_permutations(ext) {
        assert!(
            !set.contains(OsStr::new(&case)),
            "Set should NOT contain variant: {}",
            case
        );
    }
}

#[test]
fn test_audio_contains_expected() {
    let expected = [
        "aac", "ac3", "caf", "dts", "dtshd", "eac3", "ec3", "flac", "m4a", "mka", "mlp", "mp2",
        "mp3", "mpa", "opus", "ra", "thd", "truehd", "tta", "wav", "weba", "webma", "wma", "3gp",
        "av1", "avi", "f4v", "flv", "m2ts", "mkv", "mp4", "mpg", "mov", "mpeg", "ogg", "ogm",
        "ogv", "ts", "webm", "wmv",
    ];
    for ext in expected {
        assert_all_permutations_present(&AUDIO, ext);
    }
}

#[test]
fn test_video_contains_expected() {
    let expected = [
        "264", "265", "avc", "h264", "h265", "hevc", "ivf", "m2v", "mpv", "obu", "vc1", "x264",
        "x265", "m4v", "3gp", "av1", "avi", "f4v", "flv", "m2ts", "mkv", "mp4", "mpg", "mov",
        "mpeg", "ogg", "ogm", "ogv", "ts", "webm", "wmv",
    ];
    for ext in expected {
        assert_all_permutations_present(&VIDEO, ext);
    }
}

#[test]
fn test_fonts_contains_expected() {
    for ext in ["otf", "ttf"] {
        assert_all_permutations_present(&FONTS, ext);
    }
}

#[test]
fn test_matroska_contains_expected() {
    for ext in ["mka", "mks", "mkv", "webm"] {
        assert_all_permutations_present(&MATROSKA, ext);
    }
}

#[test]
fn test_subs_contains_expected() {
    for ext in ["ass", "mks", "srt", "ssa", "sub", "sup"] {
        assert_all_permutations_present(&SUBS, ext);
    }
}

#[test]
fn test_rtm_subs_contains_expected() {
    for ext in ["ass", "srt"] {
        assert_all_permutations_present(&RTM_SUBS, ext);
    }
}

#[test]
fn test_track_in_contains_expected() {
    let expected = &[
        "264", "265", "3gp", "aac", "ac3", "ass", "avi", "avc", "av1", "caf", "dts", "dtshd",
        "eac3", "ec3", "f4v", "flac", "flv", "h264", "h265", "hevc", "ivf", "m2ts", "m2v", "m4a",
        "m4v", "mka", "mks", "mlp", "mov", "mp2", "mp3", "mp4", "mpa", "mpg", "mpv", "mpeg", "ogg",
        "ogm", "ogv", "obu", "opus", "ra", "srt", "ssa", "sub", "sup", "thd", "truehd", "tta",
        "ts", "vc1", "wav", "weba", "webm", "webma", "wma", "wmv", "x264", "x265",
    ];
    for ext in expected {
        assert_all_permutations_present(&TRACK_IN, ext);
    }
}

#[test]
fn test_track_in_absent() {
    for ext in FONTS.iter() {
        assert!(!TRACK_IN.contains(ext));
    }
}

#[test]
fn test_extensions_absent() {
    let fake_exts = [
        "fake", "none", "xyz", "audiox", "v1deo", "123", "supper", "trackin", "ext", "subtitle",
    ];

    let sets = &[
        &AUDIO, &VIDEO, &FONTS, &MATROSKA, &SUBS, &RTM_SUBS, &TRACK_IN,
    ];

    for set in sets {
        for ext in fake_exts {
            assert_all_permutations_absent(set, ext);
        }
    }
}

fn generate_fake_exts(existing: &HashSet<&str>, count: usize) -> Vec<String> {
    use rand::{Rng, seq::IteratorRandom};
    use std::collections::HashSet;

    let mut rng = rand::thread_rng();
    let charset = b"abcdefghijklmnopqrstuvwxyz0123456789";
    let mut fake_exts = HashSet::new();

    while fake_exts.len() < count {
        let len = rng.gen_range(3..6);
        let candidate: String = (0..len)
            .map(|_| *charset.iter().choose(&mut rng).unwrap() as char)
            .collect();

        if !existing.contains(candidate.as_str()) {
            fake_exts.insert(candidate);
        }
    }

    fake_exts.into_iter().collect()
}

#[test]
fn test_extensions_auto_absent() {
    let all_known: HashSet<&str> = AUDIO
        .iter()
        .chain(VIDEO.iter())
        .chain(FONTS.iter())
        .chain(MATROSKA.iter())
        .chain(SUBS.iter())
        .chain(RTM_SUBS.iter())
        .chain(TRACK_IN.iter())
        .filter_map(|s| s.to_str())
        .collect();

    let fake_exts = generate_fake_exts(&all_known, 100);

    let sets = &[
        &AUDIO, &VIDEO, &FONTS, &MATROSKA, &SUBS, &RTM_SUBS, &TRACK_IN,
    ];

    for set in sets {
        for ext in &fake_exts {
            assert_all_permutations_absent(set, &ext);
        }
    }
}
