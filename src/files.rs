/*
use std::collections::HashSet;
use std::fs;

pub mod info;


pub struct Files {
    base_dir: String,
    pub extensions: FileExtensions,
    start_dir: String,
    stems: Vec<String>,
}

impl Files {
    fn find_base_dir(start_dir: &str) -> String {
        let limit_search_above = 0;
        if limit_search_above <= 0 {
            return start_dir.to_string();
        }

        start_dir.to_string()
    }

    pub fn new(start_dir: String) -> Self {
        let extensions = FileExtensions::new();
        let stems = vec!["x".to_string()];
        let base_dir = Self::find_base_dir(&start_dir);

        Self {
            base_dir,
            extensions,
            start_dir,
            stems,
        }
    }
}

pub struct FileExtensions {
    pub audio: HashSet<String>,
    pub fonts: HashSet<String>,
    pub matroska: HashSet<String>,
    pub retiming_subtitles: HashSet<String>,
    pub subtitles: HashSet<String>,
    pub video: HashSet<String>,
    pub with_tracks: HashSet<String>,
}

impl FileExtensions {
    fn get_case_combinations(ext: &str) -> HashSet<String> {
        let mut combinations = HashSet::new();
        let len = ext.len();
        let possible_combinations = 1 << len;

        for i in 0..possible_combinations {
            let mut combination = String::new();
            for (j, c) in ext.chars().enumerate() {
                if (i >> j) & 1 == 1 {
                    combination.push(c.to_ascii_uppercase());
                } else {
                    combination.push(c.to_ascii_lowercase());
                }
            }
            combinations.insert(combination);
        }

        combinations
    }

    fn get_hashset(exts: Vec<&str>) -> HashSet<String> {
        exts.iter()
            .flat_map(|ext| Self::get_case_combinations(ext))
            .collect()
    }

    pub fn new() -> Self {
        let common_on_audio_and_video = &[
            "3gp", "av1", "avi", "f4v", "flv", "m2ts", "mkv", "mp4", "mpg", "mov", "mpeg", "ogg",
            "ogm", "ogv", "ts", "webm", "wmv",
        ];

        let mut audio = vec![
            "aac", "ac3", "caf", "dts", "dtshd", "eac3", "ec3", "flac", "m4a", "mka", "mlp", "mp2",
            "mp3", "mpa", "opus", "ra", "thd", "truehd", "tta", "wav", "weba", "webma", "wma",
        ];
        audio.extend(common_on_audio_and_video);
        let audio = Self::get_hashset(audio);

        let fonts = Self::get_hashset(vec!["otf", "ttf"]);

        let matroska = Self::get_hashset(vec!["mka", "mks", "mkv", "webm"]);

        let retiming_subtitles = Self::get_hashset(vec!["ass", "srt"]);

        let subtitles = Self::get_hashset(vec!["ass", "mks", "srt", "ssa", "sub", "sup"]);

        let mut video = vec![
            "264", "265", "avc", "h264", "h265", "hevc", "ivf", "m2v", "mpv", "obu", "vc1", "x264",
            "x265", "m4v",
        ];
        video.extend(common_on_audio_and_video);
        let video = Self::get_hashset(video);

        println!("{:?}", video);

        let with_tracks: HashSet<String> = audio
            .iter()
            .chain(subtitles.iter())
            .chain(video.iter())
            .cloned()
            .collect();

        Self {
            audio,
            fonts,
            matroska,
            retiming_subtitles,
            subtitles,
            video,
            with_tracks,
        }
    }
}
*/
