use super::{super::TracksFlags, BaseTracksFlagsFields};
use crate::types::traits::ClapArgID;
use clap::{ArgMatches, Error, FromArgMatches, error::ErrorKind};

#[derive(Clone, Copy)]
pub(in crate::types) enum TracksFlagsArg {
    HelpAddDefaults,
    AddDefaults,
    NoAddDefaults,
    Defaults,
    LimDefaults,
    HelpAddForceds,
    AddForceds,
    NoAddForceds,
    Forceds,
    LimForceds,
    HelpAddEnableds,
    AddEnableds,
    NoAddEnableds,
    Enableds,
    LimEnableds,
}

impl ClapArgID for TracksFlags {
    type Arg = TracksFlagsArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            TracksFlagsArg::HelpAddDefaults => "help_add_defaults",
            TracksFlagsArg::AddDefaults => "add_defaults",
            TracksFlagsArg::NoAddDefaults => "no_add_defaults",
            TracksFlagsArg::Defaults => "defaults",
            TracksFlagsArg::LimDefaults => "lim_defaults",
            TracksFlagsArg::HelpAddForceds => "help_add_forceds",
            TracksFlagsArg::AddForceds => "add_forceds",
            TracksFlagsArg::NoAddForceds => "no_add_forceds",
            TracksFlagsArg::Forceds => "forceds",
            TracksFlagsArg::LimForceds => "lim_forceds",
            TracksFlagsArg::HelpAddEnableds => "help_add_enableds",
            TracksFlagsArg::AddEnableds => "add_enableds",
            TracksFlagsArg::NoAddEnableds => "no_add_enableds",
            TracksFlagsArg::Enableds => "enableds",
            TracksFlagsArg::LimEnableds => "lim_enableds",
        }
    }
}

impl FromArgMatches for TracksFlags {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let defaults = base_from_matches(
            matches,
            TracksFlagsArg::AddDefaults,
            TracksFlagsArg::NoAddDefaults,
            TracksFlagsArg::Defaults,
            TracksFlagsArg::LimDefaults,
        )?;
        let forceds = base_from_matches(
            matches,
            TracksFlagsArg::AddForceds,
            TracksFlagsArg::NoAddForceds,
            TracksFlagsArg::Forceds,
            TracksFlagsArg::LimForceds,
        )?;
        let enableds = base_from_matches(
            matches,
            TracksFlagsArg::AddEnableds,
            TracksFlagsArg::NoAddEnableds,
            TracksFlagsArg::Enableds,
            TracksFlagsArg::LimEnableds,
        )?;

        Ok(Self {
            defaults,
            forceds,
            enableds,
        })
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}

fn base_from_matches(
    matches: &mut ArgMatches,
    add_arg: TracksFlagsArg,
    no_add_arg: TracksFlagsArg,
    arg: TracksFlagsArg,
    lim_arg: TracksFlagsArg,
) -> Result<BaseTracksFlagsFields, Error> {
    let add = match matches
        .try_remove_one::<bool>(TracksFlags::as_str(add_arg))
        .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
    {
        Some(true) => Some(true),
        _ => {
            match matches
                .try_remove_one::<bool>(TracksFlags::as_str(no_add_arg))
                .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
            {
                Some(true) => Some(false),
                _ => None,
            }
        }
    };

    let lim_true = match matches
        .try_remove_one::<u32>(TracksFlags::as_str(lim_arg))
        .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
    {
        Some(u) => u,
        None => match arg {
            TracksFlagsArg::Defaults => TracksFlags::default_lim_true_defaults(),
            TracksFlagsArg::Forceds => TracksFlags::default_lim_true_forceds(),
            TracksFlagsArg::Enableds => TracksFlags::default_lim_true_enableds(),
            _ => {
                return Err(Error::raw(
                    ErrorKind::UnknownArgument,
                    format!("Not default limit for arg '{}'", TracksFlags::as_str(arg)),
                ));
            }
        },
    };

    let base = match matches
        .try_remove_one::<BaseTracksFlagsFields>(TracksFlags::as_str(arg))
        .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
    {
        Some(base) => base,
        None => BaseTracksFlagsFields::new(),
    }
    .add(add)
    .lim_true(lim_true);

    Ok(base)
}
