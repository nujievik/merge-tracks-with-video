use clap::{Arg, ArgMatches, Command, FromArgMatches};
use mux_media::types::Verbosity;

fn get_matches_from<I, T>(args: I) -> ArgMatches
where
    I: IntoIterator<Item = T>,
    T: Into<std::ffi::OsString> + Clone,
{
    Command::new("test")
        .arg(
            Arg::new("cnt_verbose")
                .short('v')
                .action(clap::ArgAction::Count),
        )
        .arg(
            Arg::new("quiet")
                .long("quiet")
                .action(clap::ArgAction::SetTrue),
        )
        .get_matches_from(args)
}

#[test]
fn test_default_verbosity() {
    let matches = get_matches_from(&["test"]);
    let verbosity = Verbosity::from_arg_matches(&matches).unwrap();
    assert_eq!(verbosity, Verbosity::default());
}

#[test]
fn test_quiet_flag() {
    let matches = get_matches_from(&["test", "--quiet"]);
    let verbosity = Verbosity::from_arg_matches(&matches).unwrap();
    assert_eq!(verbosity, Verbosity::Quiet);
}

#[test]
fn test_single_verbose_flag() {
    let matches = get_matches_from(&["test", "-v"]);
    let verbosity = Verbosity::from_arg_matches(&matches).unwrap();
    assert_eq!(verbosity, Verbosity::Verbose);
}

#[test]
fn test_multiple_verbose_flags() {
    let matches = get_matches_from(&["test", "-vv"]);
    let verbosity = Verbosity::from_arg_matches(&matches).unwrap();
    assert_eq!(verbosity, Verbosity::Debug);
}

#[test]
fn test_update_from_arg_matches() {
    let matches = get_matches_from(&["test", "--quiet"]);
    let mut verbosity = Verbosity::default();
    verbosity.update_from_arg_matches(&matches).unwrap();
    assert_eq!(verbosity, Verbosity::Quiet);
}
