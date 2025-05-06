use super::super::TracksNames;
use crate::types::traits::ClapArgID;
use clap::{ArgMatches, Error, FromArgMatches, error::ErrorKind};

#[derive(Clone, Copy)]
pub(in crate::types) enum TracksNamesArg {
    HelpAddNames,
    AddNames,
    NoAddNames,
    Names,
}

impl ClapArgID for TracksNames {
    type Arg = TracksNamesArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            TracksNamesArg::HelpAddNames => "help_add_names",
            TracksNamesArg::AddNames => "add_names",
            TracksNamesArg::NoAddNames => "no_add_names",
            TracksNamesArg::Names => "names",
        }
    }
}

impl FromArgMatches for TracksNames {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let add = match matches
            .try_remove_one::<bool>(TracksNames::as_str(TracksNamesArg::AddNames))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(true) => Some(true),
            _ => {
                match matches
                    .try_remove_one::<bool>(TracksNames::as_str(TracksNamesArg::NoAddNames))
                    .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
                {
                    Some(true) => Some(false),
                    _ => None,
                }
            }
        };

        let names = match matches
            .try_remove_one::<TracksNames>(TracksNames::as_str(TracksNamesArg::Names))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(names) => names,
            None => TracksNames::new(),
        }
        .add(add);

        Ok(names)
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
