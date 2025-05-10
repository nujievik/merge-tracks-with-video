use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error};
use globset::GlobSet;

pub struct Retiming {
    pub rm_segments: Option<GlobSet>,
    pub no_linked: bool,
    pub less: bool,
}

impl Retiming {
    fn default_no_linked() -> bool {
        false
    }

    fn default_less() -> bool {
        false
    }
}

pub enum RetimingArg {
    RmSegments,
    NoLinked,
    Less,
}

impl ClapArgID for Retiming {
    type Arg = RetimingArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            RetimingArg::RmSegments => "rm_segments",
            RetimingArg::NoLinked => "no_linked",
            RetimingArg::Less => "less_retiming",
        }
    }
}

impl clap::FromArgMatches for Retiming {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let rm_segments = val_from_matches!(matches, GlobSet, RetimingArg::RmSegments, @no_default);
        let no_linked = val_from_matches!(
            matches,
            bool,
            RetimingArg::NoLinked,
            Self::default_no_linked
        );
        let less = val_from_matches!(matches, bool, RetimingArg::Less, Self::default_less);

        Ok(Self {
            rm_segments,
            no_linked,
            less,
        })
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
