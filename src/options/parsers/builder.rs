use super::value;
use crate::{LanguageCode, RangeMux};
use clap::builder::ValueParser;
use clap::{Arg, ArgAction, Command};
use std::str::FromStr;

const U32_MAX_STR: &str = "4294967295";

pub struct Untarget;

impl Untarget {
    pub fn new() -> Command {
        let cmd = init();
        let cmd = add_file_paths_options(cmd);
        let cmd = add_global_options(cmd);
        let cmd = InverseOnProMode::add_to(cmd);
        let cmd = add_retiming_options(cmd);
        let cmd = add_target_options(cmd);
        let cmd = add_call_tools(cmd);
        add_help_and_version(cmd)
    }
}

pub struct Target;

impl Target {
    pub fn new() -> Command {
        let cmd = init();
        add_help_and_version(cmd)
    }
}

fn init() -> clap::Command {
    clap::Command::new(env!("CARGO_PKG_NAME"))
        .no_binary_name(true)
        .version(concat!("v", env!("CARGO_PKG_VERSION")))
        .disable_help_flag(true)
        .disable_version_flag(true)
        .override_usage(concat!(env!("CARGO_PKG_NAME"), " [options]"))
}

fn add_file_paths_options(cmd: Command) -> Command {
    cmd.next_help_heading("File paths options")
        .arg(
            Arg::new("start_dir")
                .short('i')
                .long("input")
                .aliases(["start-directory", "start-dir"])
                .value_name("dir")
                .help("File search start directory")
                .value_parser(ValueParser::new(value::StartDirParser))
                .default_value(".")
                .hide_default_value(true),
        )
        .arg(
            Arg::new("output")
                .short('o')
                .long("output")
                .value_name("out[,put]")
                .help("Output paths pattern: out{num}[put]")
                .value_parser(ValueParser::new(value::OutputParser)),
        )
        .arg(
            Arg::new("range_mux")
                .short('r')
                .long("range")
                .alias("range-mux")
                .value_name("[n][,m]")
                .help("Number range of file names to mux")
                .value_parser(ValueParser::new(RangeMux::from_str))
                .default_value("0..")
                .hide_default_value(true),
        )
        .arg(
            Arg::new("lim_mux")
                .long("lim")
                .aliases(&["limit-mux", "lim-mux", "limit"])
                .value_name("n")
                .help("Max number of muxed files to create")
                .value_parser(clap::value_parser!(u32).range(1..))
                .default_value(U32_MAX_STR)
                .hide_default_value(true),
        )
        .arg(
            Arg::new("lim_upward")
                .long("upward")
                .aliases(["limit-upward", "lim-upward"])
                .value_name("n")
                .help("Max directory levels to search upward")
                .value_parser(clap::value_parser!(u32))
                .default_value("8")
                .hide_default_value(true),
        )
        .arg(
            Arg::new("lim_check")
                .long("check")
                .aliases(["limit-check", "lim-check"])
                .value_name("n")
                .help("Max files to check per directory level")
                .value_parser(clap::value_parser!(u32).range(1..))
                .default_value("128")
                .hide_default_value(true),
        )
        .arg(
            Arg::new("skip_patterns")
                .long("skip")
                .alias("skip-patterns")
                .value_name("n[,m]...")
                .help("Skip patterns")
                .value_parser(ValueParser::new(value::parse_patterns)),
        )
}

fn add_global_options(cmd: Command) -> Command {
    cmd.next_help_heading("Global options")
        .arg(
            Arg::new("verbose")
                .short('v')
                .long("verbose")
                .help("Increase verbosity")
                .action(ArgAction::Count),
        )
        .arg(
            Arg::new("quiet")
                .short('q')
                .long("quiet")
                .help("Suppress logging")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("locale")
                .long("locale")
                .value_name("lng")
                .help("Locale language (on logging and sort)")
                .value_parser(ValueParser::new(LanguageCode::from_str)),
        )
        .arg(
            Arg::new("exit-on-err")
                .long("exit-on-err")
                .alias("exit-on-error")
                .help("Skip mux for next files")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("pro_mode")
                .short('p')
                .long("pro")
                .alias("pro-mode")
                .help("Enable Pro-mode")
                .action(ArgAction::SetTrue),
        )
}

struct InverseOnProMode;

impl InverseOnProMode {
    const OPTIONS: &'static [(
        &'static str, // Arg_help
        &'static str, // Help left
        &'static str, // Help right
        &'static str, // Arg_true
        &'static str, // Opt_true
        &'static str, // Arg_false
        &'static str, // Opt_false
    )] = &[
        (
            "defaults_help",
            "defaults / --no-defaults",
            "Auto/Man set default-track-flag's",
            "defaults",
            "defaults",
            "no_defaults",
            "no-defaults",
        ),
        (
            "forceds_help",
            "forceds / --no-forseds",
            "Auto/Man set forced-display-flag's",
            "forceds",
            "forceds",
            "no_forseds",
            "no-forceds",
        ),
        (
            "languages_help",
            "languages / --no-languages",
            "Auto/Man set language's",
            "languages",
            "languages",
            "no_languages",
            "no-languages",
        ),
        (
            "sub_charsets_help",
            "sub-charsets / --no-sub-charsets",
            "Auto/Man set sub-charset's",
            "sub_charsets",
            "sub-charsets",
            "no_sub_charsets",
            "no-sub-charsets",
        ),
        (
            "enableds_help",
            "enableds / --no-enableds",
            "Auto/Man set track-enabled-flag's",
            "enableds",
            "enableds",
            "no_enableds",
            "no-enableds",
        ),
        (
            "names_help",
            "names / --no-names",
            "Auto/Man set track-name's",
            "names",
            "names",
            "no_names",
            "no-names",
        ),
        (
            "orders_help",
            "orders / --no-orders",
            "Auto/Man set track-order's",
            "orders",
            "orders",
            "no_orders",
            "no-orders",
        ),
        (
            "sort_fonts_help",
            "sort-fonts / --no-sort-fonts",
            "On/Off sorting in-files fonts",
            "sort_fonts",
            "sort-fonts",
            "no_sort_fonts",
            "no-sort-fonts",
        ),
    ];

    fn add_to(cmd: Command) -> Command {
        let mut cmd = cmd.next_help_heading("Inverse on Pro-mode");

        for (help_arg, help_left, help_right, arg, opt, no_arg, no_opt) in Self::OPTIONS {
            cmd = cmd
                .arg(
                    Arg::new(help_arg)
                        .long(help_left)
                        .help(help_right)
                        .action(ArgAction::SetTrue),
                )
                .arg(
                    Arg::new(arg)
                        .long(opt)
                        .action(ArgAction::SetTrue)
                        .hide(true),
                )
                .arg(
                    Arg::new(no_arg)
                        .long(no_opt)
                        .action(ArgAction::SetFalse)
                        .overrides_with(arg)
                        .hide(true),
                )
        }

        cmd
    }
}

fn add_retiming_options(cmd: Command) -> Command {
    cmd.next_help_heading("Retiming options")
        .arg(
            Arg::new("remove_segments")
                .long("rm-segments")
                .alias("remove-segments")
                .value_name("n[,m]...")
                .help("Remove segments with names n,m etc.")
                .value_parser(ValueParser::new(value::parse_patterns)),
        )
        .arg(
            Arg::new("no_linked")
                .long("no-linked")
                .help("Remove linked segments")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("less_retiming")
                .long("less-retiming")
                .help("No retiming if linked segments outside main")
                .action(ArgAction::SetTrue),
        )
}

fn add_target_options(cmd: Command) -> Command {
    cmd.next_help_heading("Target options")
        .arg(
            Arg::new("target_help")
                .short('t')
                .long("target <trg> [options]")
                .help("Set next options for target")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("target_list")
                .long("target --list")
                .help("Print supported targets"),
        )
        .arg(
            Arg::new("target_exclude_help")
                .long("target <trg> --no-files")
                .help("Exclude trg files (no global trg)")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("audio_tracks")
                .short('a')
                .long("audio")
                .alias("audio-tracks")
                .value_name("n[,m]...")
                .help("Copy audio tracks n,m etc."),
        )
        .arg(
            Arg::new("no_audio")
                .short('A')
                .long("no-audio")
                .help("Don't copy any audio track")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("video_tracks")
                .short('d')
                .long("video")
                .alias("video-tracks")
                .value_name("n[,m]...")
                .help("Copy video tracks n,m etc."),
        )
        .arg(
            Arg::new("no_video")
                .short('D')
                .long("no-video")
                .help("Don't copy any video track")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("sub_tracks")
                .short('s')
                .long("subs")
                .aliases(["subtitle-tracks", "subtitles"])
                .value_name("n[,m]...")
                .help("Copy subtitle tracks n,m etc."),
        )
        .arg(
            Arg::new("no_subs")
                .short('S')
                .long("no-subs")
                .alias("no-subtitles")
                .help("Don't copy any subtitle track")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("no_attachs")
                .short('M')
                .long("no-attachs")
                .alias("no-attachments")
                .help("Don't copy any attachment")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("no_fonts")
                .short('F')
                .long("no-fonts")
                .help("Don't copy any font")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("no_chapters")
                .long("no-chapters")
                .help("Don't keep chapters")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("default")
                .long("default")
                .alias("default-track-flag")
                .value_name("B or n[:B][,m:B]...")
                .help("Bool default-track-flag"),
        )
        .arg(
            Arg::new("lim_default")
                .long("lim-default")
                .aliases([
                    "limit-default-track-flag",
                    "lim-default-track-flag",
                    "limit-default",
                ])
                .help("Max true default-track-flag's")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("forced")
                .long("forced")
                .alias("forced-display-flag")
                .value_name("B or n[:B][,m:B]...")
                .help("Bool forced-display-flag"),
        )
        .arg(
            Arg::new("lim_forced")
                .long("lim-forced")
                .aliases([
                    "limit-forced-display-flag",
                    "lim-forced-display-flag",
                    "limit-forced",
                ])
                .help("Max true forced-display-flag's")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("enabled")
                .long("enabled")
                .alias("track-enabled-flag")
                .value_name("B or n[:B][,m:B]...")
                .help("Bool track-enabled-flag"),
        )
        .arg(
            Arg::new("lim_enabled")
                .long("lim-enabled")
                .aliases([
                    "limit-track-enabled-flag",
                    "lim-track-enabled-flag",
                    "limit-enabled",
                ])
                .help("Max true track-enabled-flag's")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("name")
                .long("name")
                .alias("track-name")
                .value_name("N or n:N[,m:N]...")
                .help("Track name"),
        )
        .arg(
            Arg::new("language")
                .long("lang")
                .alias("language")
                .value_name("L or n:L[,m:L]...")
                .help("Track language"),
        )
        .arg(
            Arg::new("specials")
                .long("specials")
                .value_name("spl")
                .help("Set unpresented mkvmerge options"),
        )
}

fn add_call_tools(cmd: Command) -> Command {
    cmd.next_help_heading("Other options")
        .arg(
            Arg::new("ffprobe_help")
                .long("ffprobe [options]")
                .help("Call ffprobe")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("mkvextract")
                .long("mkvextract [options]")
                .help("Call mkvextract")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("mkvinfo_help")
                .long("mkvinfo [options]")
                .help("Call mkvinfo")
                .action(ArgAction::SetTrue),
        )
        .arg(
            Arg::new("mkvmerge_help")
                .long("mkvmerge [options]")
                .help("Call mkvmerge")
                .action(ArgAction::SetTrue),
        )
}

fn add_help_and_version(cmd: Command) -> Command {
    cmd.next_help_heading("Other options")
        .arg(
            Arg::new("help")
                .short('h')
                .long("help")
                .help("Show help")
                .action(ArgAction::Help),
        )
        .arg(
            Arg::new("version")
                .short('V')
                .long("version")
                .help("Show version")
                .action(ArgAction::Version),
        )
}
