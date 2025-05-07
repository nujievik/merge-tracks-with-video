use crate::types::AppError;
use std::path::PathBuf;
use std::str::FromStr;

#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub enum TargetGroup {
    Audio,
    Video,
    Signs,
    Subs,
}

#[derive(Clone, PartialEq, Eq, Hash)]
pub enum Target {
    Group(TargetGroup),
    Path(PathBuf),
}

impl FromStr for TargetGroup {
    type Err = AppError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(match s.trim() {
            "a" => Self::Audio,
            "audio" => Self::Audio,
            "v" => Self::Video,
            "video" => Self::Video,
            "signs" => Self::Signs,
            "s" => Self::Subs,
            "subs" => Self::Subs,
            "subtitles" => Self::Subs,
            _ => {
                return Err(AppError::from(format!(
                    "Unrecognized target group: '{}'",
                    s
                )));
            }
        })
    }
}
