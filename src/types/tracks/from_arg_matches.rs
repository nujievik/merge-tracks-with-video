use super::{BaseTracksFields, Tracks, TracksFlags, TracksLangs, TracksNames};
use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error};

pub enum TracksArg {
    Audio,
    NoAudio,
    Subs,
    NoSubs,
    Video,
    NoVideo,
    Buttons,
    NoButtons,
}

impl ClapArgID for Tracks {
    type Arg = TracksArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            TracksArg::Audio => "audio",
            TracksArg::NoAudio => "no_audio",
            TracksArg::Subs => "subs",
            TracksArg::NoSubs => "no_subs",
            TracksArg::Video => "video",
            TracksArg::NoVideo => "no_video",
            TracksArg::Buttons => "buttons",
            TracksArg::NoButtons => "no_buttons",
        }
    }
}

impl clap::FromArgMatches for Tracks {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let audio = Self::base_from_matches(matches, TracksArg::Audio, TracksArg::NoAudio)?;
        let subs = Self::base_from_matches(matches, TracksArg::Subs, TracksArg::NoSubs)?;
        let video = Self::base_from_matches(matches, TracksArg::Video, TracksArg::NoVideo)?;
        let buttons = Self::base_from_matches(matches, TracksArg::Buttons, TracksArg::NoButtons)?;

        let flags = TracksFlags::from_arg_matches_mut(matches)?;
        let names = TracksNames::from_arg_matches_mut(matches)?;
        let langs = TracksLangs::from_arg_matches_mut(matches)?;

        Ok(Self {
            audio,
            subs,
            video,
            buttons,
            flags,
            names,
            langs,
        })
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}

impl Tracks {
    fn base_from_matches(
        matches: &mut ArgMatches,
        arg: TracksArg,
        no_arg: TracksArg,
    ) -> Result<BaseTracksFields, Error> {
        Ok(
            if val_from_matches!(matches, bool, no_arg, BaseTracksFields::default_no_flag) {
                BaseTracksFields::new().no_flag(true)
            } else {
                val_from_matches!(matches, BaseTracksFields, arg, BaseTracksFields::new)
            },
        )
    }
}
