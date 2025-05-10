use super::Input;
use crate::types::{AppError, RangeU32};
use crate::{traits::ClapArgID, val_from_matches};
use clap::{ArgMatches, Error};
use globset::GlobSet;
use std::path::PathBuf;

pub enum InputArg {
    Dir,
    Range,
    Up,
    Check,
    Skip,
}

impl ClapArgID for Input {
    type Arg = InputArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            InputArg::Dir => "input",
            InputArg::Range => "range",
            InputArg::Up => "up",
            InputArg::Check => "check",
            InputArg::Skip => "skip",
        }
    }
}

impl clap::FromArgMatches for Input {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let dir = val_from_matches!(
            matches,
            PathBuf,
            InputArg::Dir,
            Self::default_dir,
            try_default
        );

        let range = val_from_matches!(matches, RangeU32, InputArg::Range, Self::default_range);
        let up = val_from_matches!(matches, u32, InputArg::Up, Self::default_up);
        let check = val_from_matches!(matches, u32, InputArg::Check, Self::default_check);
        let skip = val_from_matches!(matches, GlobSet, InputArg::Skip, @no_default);

        Ok(Self {
            dir,
            range,
            up,
            check,
            skip,
            topmost: None,
        }
        .try_topmost()?)
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
