use super::{super::TracksFlags, BaseTracksFlagsFields};
use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error};

#[derive(Clone, Copy)]
pub enum TracksFlagsArg {
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

impl clap::FromArgMatches for TracksFlags {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let defaults = Self::base_from_matches(
            matches,
            TracksFlagsArg::AddDefaults,
            TracksFlagsArg::NoAddDefaults,
            TracksFlagsArg::Defaults,
            TracksFlagsArg::LimDefaults,
        )?;
        let forceds = Self::base_from_matches(
            matches,
            TracksFlagsArg::AddForceds,
            TracksFlagsArg::NoAddForceds,
            TracksFlagsArg::Forceds,
            TracksFlagsArg::LimForceds,
        )?;
        let enableds = Self::base_from_matches(
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

impl TracksFlags {
    fn base_from_matches(
        matches: &mut ArgMatches,
        add_arg: TracksFlagsArg,
        no_add_arg: TracksFlagsArg,
        arg: TracksFlagsArg,
        lim_arg: TracksFlagsArg,
    ) -> Result<BaseTracksFlagsFields, Error> {
        let add = val_from_matches!(matches, bool, add_arg, no_add_arg, @off_on_pro);
        let lim_true = match val_from_matches!(matches, u32, lim_arg, @no_default) {
            Some(u) => u,
            None => match arg {
                TracksFlagsArg::Defaults => TracksFlags::default_lim_true_defaults(),
                TracksFlagsArg::Forceds => TracksFlags::default_lim_true_forceds(),
                TracksFlagsArg::Enableds => TracksFlags::default_lim_true_enableds(),
                _ => Err(AppError::from(format!(
                    "No found default limit for arg '{}'",
                    TracksFlags::as_str(arg)
                )))?,
            },
        };

        Ok(val_from_matches!(
            matches,
            BaseTracksFlagsFields,
            arg,
            BaseTracksFlagsFields::new
        )
        .add(add)
        .lim_true(lim_true))
    }
}
