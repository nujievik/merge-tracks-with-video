use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error};
use std::sync::Once;

static ENV_LOGGER: Once = Once::new();

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

    pub fn set_env_logger(&self) {
        let level = self.to_level_filter();
        ENV_LOGGER.call_once(|| {
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
        Ok(
            if val_from_matches!(matches, bool, VerbosityArg::Quiet, @no_default).unwrap_or(false) {
                Self::Quiet
            } else if let Some(cnt) =
                val_from_matches!(matches, u8, VerbosityArg::Verbose, @no_default)
            {
                Self::from_count(cnt)
            } else {
                Self::default()
            },
        )
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
