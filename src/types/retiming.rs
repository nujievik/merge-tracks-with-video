use crate::types::traits::ClapArgID;
use clap::error::ErrorKind;
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

pub(in crate::types) enum RetimingArg {
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
        let rm_segments = matches
            .try_remove_one::<GlobSet>(Self::as_str(RetimingArg::RmSegments))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?;

        let no_linked = match matches
            .try_remove_one::<bool>(Self::as_str(RetimingArg::NoLinked))
            .map_err(|e| Error::raw(ErrorKind::ValueValidation, e.to_string()))?
        {
            Some(b) => b,
            None => Self::default_no_linked(),
        };

        let less = match matches
            .try_remove_one::<bool>(Self::as_str(RetimingArg::Less))
            .map_err(|e| Error::raw(ErrorKind::ValueValidation, e.to_string()))?
        {
            Some(b) => b,
            None => Self::default_less(),
        };

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
