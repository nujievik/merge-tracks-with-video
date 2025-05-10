use super::super::TracksLangs;
use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error};

#[derive(Clone, Copy)]
pub enum TracksLangsArg {
    HelpAddLangs,
    AddLangs,
    NoAddLangs,
    Langs,
}

impl ClapArgID for TracksLangs {
    type Arg = TracksLangsArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            TracksLangsArg::HelpAddLangs => "help_add_langs",
            TracksLangsArg::AddLangs => "add_langs",
            TracksLangsArg::NoAddLangs => "no_add_langs",
            TracksLangsArg::Langs => "langs",
        }
    }
}

impl clap::FromArgMatches for TracksLangs {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let add = val_from_matches!(matches, bool, TracksLangsArg::AddLangs, TracksLangsArg::NoAddLangs, @off_on_pro);
        Ok(val_from_matches!(matches, Self, TracksLangsArg::Langs, Self::new).add(add))
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
