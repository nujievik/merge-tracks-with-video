use super::Specials;
use crate::types::traits::ClapArgID;
use clap::{ArgMatches, Error, FromArgMatches, error::ErrorKind};

#[derive(Clone, Copy)]
pub(in crate::types) enum SpecialsArg {
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
        let specials = match matches
            .try_remove_one::<Specials>(Specials::as_str(SpecialsArg::Specials))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(spls) => spls,
            None => Specials::new(),
        };

        Ok(specials)
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
