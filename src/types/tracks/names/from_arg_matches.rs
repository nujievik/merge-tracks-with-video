use super::super::TracksNames;
use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error};

#[derive(Clone, Copy)]
pub enum TracksNamesArg {
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

impl clap::FromArgMatches for TracksNames {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let add = val_from_matches!(matches, bool, TracksNamesArg::AddNames, TracksNamesArg::NoAddNames, @off_on_pro);
        Ok(val_from_matches!(matches, Self, TracksNamesArg::Names, Self::new).add(add))
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
