use super::Specials;
use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error, FromArgMatches};

#[derive(Clone, Copy)]
pub enum SpecialsArg {
    Specials,
}

impl ClapArgID for Specials {
    type Arg = SpecialsArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            SpecialsArg::Specials => "specials",
        }
    }
}

impl FromArgMatches for Specials {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        Ok(val_from_matches!(
            matches,
            Specials,
            SpecialsArg::Specials,
            Self::new
        ))
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
