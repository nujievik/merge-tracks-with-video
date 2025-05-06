use crate::types::traits::ClapArgID;
use clap::{ArgMatches, Error};
use std::sync::Once;

static INIT_LOGGER: Once = Once::new();

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Verbosity {
    Quiet,
    Normal,
    Verbose,
    Debug,
}

impl Default for Verbosity {
    fn default() -> Self {
        Verbosity::Normal
    }
}

impl Verbosity {
    pub fn from_count(count: u8) -> Self {
        match count {
            0 => Verbosity::default(),
            1 => Verbosity::Verbose,
            _ => Verbosity::Debug,
        }
    }

    pub fn init_env_logger(&self) {
        let level = self.to_level_filter();
        INIT_LOGGER.call_once(|| {
            env_logger::Builder::new().filter_level(level).init();
        });
    }

    fn to_level_filter(&self) -> log::LevelFilter {
        match self {
            Verbosity::Quiet => log::LevelFilter::Error,
            Verbosity::Normal => log::LevelFilter::Info,
            Verbosity::Verbose => log::LevelFilter::Debug,
            Verbosity::Debug => log::LevelFilter::Trace,
        }
    }
}

pub enum VerbosityArg {
    Verbose,
    Quiet,
}

impl ClapArgID for Verbosity {
    type Arg = VerbosityArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            VerbosityArg::Verbose => "cnt_verbose",
            VerbosityArg::Quiet => "quiet",
        }
    }
}

impl clap::FromArgMatches for Verbosity {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let quiet = Self::as_str(VerbosityArg::Quiet);
        if matches.try_contains_id(quiet).unwrap_or(false) && matches.get_flag(quiet) {
            return Ok(Self::Quiet);
        }

        let verbose = Self::as_str(VerbosityArg::Verbose);
        match matches.try_contains_id(verbose) {
            Ok(true) => Ok(Self::from_count(matches.get_count(verbose))),
            Ok(false) => Ok(Self::default()),
            Err(_) => {
                eprintln!(
                    "Warning: matches does not contain id '{}'. Use default",
                    verbose
                );
                Ok(Self::default())
            }
        }
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
