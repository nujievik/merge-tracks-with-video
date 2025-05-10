mod clap_arg_id;
mod cmd_factory;
mod from_arg_matches;
pub mod raw;
mod try_from;

use crate::types::{
    Attachs, Chapters, Input, LangCode, Output, Retiming, Specials, Tracks, Verbosity,
};

pub struct AppConfig {
    pub input: Input,
    pub output: Output,
    pub verbosity: Verbosity,
    pub locale: LangCode,
    pub exit_on_err: bool,
    pub retiming: Retiming,
    pub tracks: Tracks,
    pub chapters: Chapters,
    pub attachs: Attachs,
    pub specials: Specials,
}

impl AppConfig {
    fn default_exit_on_err() -> bool {
        false
    }

    fn default_pro() -> bool {
        false
    }
}
