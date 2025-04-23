mod parse;
mod parsers;
mod raw;

use crate::{Output, RangeMux, Verbosity};
use globset::GlobSet;
use std::path::PathBuf;

pub struct Options {
    // === File paths options ===
    pub start_dir: PathBuf,
    pub output: Output,
    pub range_mux: RangeMux,
    pub lim_mux: u32,
    pub lim_upward: u32,
    pub lim_check: u32,
    pub skip_patterns: GlobSet,

    // === Global options ===
    pub verbosity: Verbosity,
    pub locale: String,
    pub exit_on_err: bool,
    pub pro_mode: bool,

    // === Retiming options ===
    pub remove_segments: GlobSet,
    pub no_linked: bool,
    pub less_retiming: bool,
}

impl Options {
    pub fn init() -> Self {
        let raw = raw::Raw::new();
        let parser = parsers::Untarget::new();
        let matches = parser.clone().get_matches_from(raw.untarget);

        let verbosity = parse::verbosity(&matches);
        crate::i18n::init_env_logger(&verbosity);

        let options = parse::untarget_matches(matches, parser, verbosity);

        options
    }
}
