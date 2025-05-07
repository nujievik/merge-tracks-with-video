use super::super::TracksLangs;
use crate::types::traits::ClapArgID;
use clap::{ArgMatches, Error, FromArgMatches, error::ErrorKind};

#[derive(Clone, Copy)]
pub(in crate::types) enum TracksLangsArg {
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

impl FromArgMatches for TracksLangs {
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
            .try_remove_one::<bool>(TracksLangs::as_str(TracksLangsArg::AddLangs))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(true) => Some(true),
            _ => {
                match matches
                    .try_remove_one::<bool>(TracksLangs::as_str(TracksLangsArg::NoAddLangs))
                    .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
                {
                    Some(true) => Some(false),
                    _ => None,
                }
            }
        };

        let names = match matches
            .try_remove_one::<TracksLangs>(TracksLangs::as_str(TracksLangsArg::Langs))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(names) => names,
            None => TracksLangs::new(),
        }
        .add(add);

        Ok(names)
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
