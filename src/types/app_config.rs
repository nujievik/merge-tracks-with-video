mod clap_arg_id;
mod cmd_factory;
mod from_arg_matches;
pub mod raw;

use crate::types::{Attachs, Chapters, Input, LangCode, Output, Retiming, Tracks, Verbosity};

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
}

/*
use crate::types::{AppFlow, Attachs, LangCode, Output, RangeU32, TrackFlags, Tracks, Verbosity};
use clap::ArgMatches;
use globset::GlobSet;
use std::path::PathBuf;

trait CfgClap {
    fn id(&self) -> &'static str;
    fn aux_id_no(&self) -> &'static str;
    fn aux_pro() -> &'static str;
    fn aux_id_add(&self) -> &'static str;
    fn aux_id_no_add(&self) -> &'static str;
    fn aux_id_lim(&self) -> &'static str;
}

pub struct AppConfig {
    // === File paths options ===
    pub start_dir: PathBuf,
    pub output: Output,
    pub range_mux: RangeU32,
    pub lim_mux: u32,
    pub lim_upward: u32,
    pub lim_check: u32,
    pub skip: GlobSet,

    // === Global options ===
    pub verbosity: Verbosity,
    pub locale: LangCode,
    pub exit_on_err: bool,

    // === Retiming options ===
    pub rm_segments: GlobSet,
    pub no_linked: bool,
    pub less_retiming: bool,

    // === Target options ===
    pub a_tracks: Tracks,
    pub v_tracks: Tracks,
    pub s_tracks: Tracks,
    pub b_tracks: Tracks,
    pub attachs: Attachs,
    pub fonts: Attachs,
    pub defaults: TrackFlags,
    pub forceds: TrackFlags,
    pub enableds: TrackFlags,
}

impl AppConfig {
    pub fn from_matches(
        matches: ArgMatches,
        verbosity: Verbosity,
        locale: LangCode,
    ) -> AppFlow<Self> {
        use fields::CfgField;
        use from_matches as fm;

        let start_dir = fm::start_dir(&matches);
        let pro = matches.get_flag(CfgField::aux_pro());

        let cfg = Self {
            output: unwrap_or_return!(fm::output(&matches, &start_dir)),
            start_dir,
            range_mux: fm::range_mux(&matches),
            lim_mux: fm::lim_mux(&matches),
            lim_upward: fm::lim_upward(&matches),
            lim_check: fm::lim_check(&matches),
            skip: fm::skip(&matches),

            verbosity,
            locale,
            exit_on_err: matches.get_flag(CfgField::ExitOnErr.id()),

            rm_segments: fm::rm_segments(&matches),
            no_linked: matches.get_flag(CfgField::NoLinked.id()),
            less_retiming: matches.get_flag(CfgField::LessRetiming.id()),

            a_tracks: fm::tracks(&matches, CfgField::ATracks),
            v_tracks: fm::tracks(&matches, CfgField::VTracks),
            s_tracks: fm::tracks(&matches, CfgField::STracks),
            b_tracks: fm::tracks(&matches, CfgField::BTracks),
            attachs: fm::attachs(&matches, CfgField::Attachs),
            fonts: fm::attachs(&matches, CfgField::Fonts),

            defaults: fm::track_flags(&matches, CfgField::Defaults, pro),
            forceds: fm::track_flags(&matches, CfgField::Forceds, pro),
            enableds: fm::track_flags(&matches, CfgField::Enableds, pro),
        };

        AppFlow::Proceed(cfg)
    }
}
*/
