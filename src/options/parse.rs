use super::Options;
use crate::get_msg;
use crate::{Output, RangeMux, Verbosity};

use clap::{ArgMatches, Command};
use globset::{GlobSet, GlobSetBuilder};
use log::error;
use std::ffi::OsString;
use std::path::{MAIN_SEPARATOR, PathBuf};
use std::process::exit;

pub(in crate::options) fn untarget_matches(
    matches: ArgMatches,
    parser: Command,
    verbosity: Verbosity,
) -> Options {
    let start_dir = start_dir(&matches);
    let locale = "rus".to_string();

    Options {
        output: output(&matches, &parser, &start_dir),
        start_dir,
        range_mux: range_mux(&matches),
        lim_mux: lim_mux(&matches),
        lim_upward: lim_upward(&matches),
        lim_check: lim_check(&matches),
        skip_patterns: skip_patterns(&matches),

        locale,
        verbosity,
        exit_on_err: matches.get_flag("exit-on-err"),
        pro_mode: matches.get_flag("pro_mode"),

        remove_segments: remove_segments(&matches),
        no_linked: matches.get_flag("no_linked"),
        less_retiming: matches.get_flag("less_retiming"),
    }
}

fn start_dir(matches: &ArgMatches) -> PathBuf {
    match matches.get_one::<PathBuf>("start_dir").cloned() {
        Some(path) => path,
        None => {
            error!("{}", get_msg("fail-get-sdir", None));
            exit(1);
        }
    }
}

fn output(matches: &ArgMatches, parser: &Command, start_dir: &PathBuf) -> Output {
    match matches.get_one::<Output>("output").cloned() {
        Some(out) => out,
        None => {
            let mut dir = start_dir.join("merged").into_os_string();
            dir.push(MAIN_SEPARATOR.to_string());

            let args: Vec<OsString> = vec!["-o".into(), dir];
            let matches = parser.clone().get_matches_from(args);

            match matches.get_one::<Output>("output").cloned() {
                Some(out) => out,
                None => {
                    error!("{}", get_msg("fail-get-out", None));
                    exit(1);
                }
            }
        }
    }
}

fn range_mux(matches: &ArgMatches) -> RangeMux {
    matches
        .get_one::<RangeMux>("range_mux")
        .cloned()
        .unwrap_or_else(RangeMux::new)
}

fn lim_mux(matches: &ArgMatches) -> u32 {
    matches
        .get_one::<u32>("lim_mux")
        .copied()
        .unwrap_or(u32::MAX)
}

fn lim_upward(matches: &ArgMatches) -> u32 {
    matches.get_one::<u32>("lim_upward").copied().unwrap_or(8)
}

fn lim_check(matches: &ArgMatches) -> u32 {
    matches.get_one::<u32>("lim_check").copied().unwrap_or(128)
}

fn default_patterns(s: &str) -> GlobSet {
    GlobSetBuilder::new().build().unwrap_or_else(|e| {
        let msg = get_msg(
            "fail-init-patterns",
            Some(&[("s", s), ("e", &e.to_string())]),
        );
        error!("{}", msg);
        exit(1);
    })
}

fn skip_patterns(matches: &ArgMatches) -> GlobSet {
    matches
        .get_one::<GlobSet>("skip_patterns")
        .cloned()
        .unwrap_or_else(|| default_patterns("skip"))
}

pub(in crate::options) fn verbosity(matches: &ArgMatches) -> Verbosity {
    if matches.get_flag("quiet") {
        Verbosity::Quiet
    } else {
        let count = matches.get_count("verbose");
        Verbosity::from_count(count)
    }
}

fn remove_segments(matches: &ArgMatches) -> GlobSet {
    matches
        .get_one::<GlobSet>("remove_segments")
        .cloned()
        .unwrap_or_else(|| default_patterns("remove-segments"))
}
