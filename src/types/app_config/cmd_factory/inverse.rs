use super::Blocks;
use crate::types::tracks::flags::from_arg_matches::TracksFlagsArg;
use crate::types::tracks::names::from_arg_matches::TracksNamesArg;
use crate::types::tracks::{TracksFlags, TracksNames};
use crate::types::traits::ClapArgID;
use clap::{Arg, ArgAction};

impl Blocks {
    pub fn inverse(mut self) -> Self {
        let mut cmd = self.cmd.next_help_heading("Inverse on Pro");

        for help in TracksFlagsArg::iter_help()
            .map(AnyTrackArg::Flag)
            .chain(TracksNamesArg::iter_help().map(AnyTrackArg::Name))
        {
            let add = help.help_to_add();
            let add_str = add.as_str();
            let no_add = help.help_to_no_add();

            cmd = cmd
                .arg(
                    Arg::new(help.as_str())
                        .long(help.long())
                        .help(help.help())
                        .action(ArgAction::SetTrue),
                )
                .arg(
                    Arg::new(add_str)
                        .long(add.long())
                        .action(ArgAction::SetTrue)
                        .hide(true),
                )
                .arg(
                    Arg::new(no_add.as_str())
                        .long(no_add.long())
                        .action(ArgAction::SetTrue)
                        .hide(true)
                        .conflicts_with(add_str),
                );
        }

        self.cmd = cmd;
        self
    }
}

enum AnyTrackArg {
    Flag(TracksFlagsArg),
    Name(TracksNamesArg),
}

impl AnyTrackArg {
    fn help_to_add(&self) -> Self {
        match self {
            AnyTrackArg::Flag(f) => AnyTrackArg::Flag(f.help_to_add()),
            AnyTrackArg::Name(n) => AnyTrackArg::Name(n.help_to_add()),
        }
    }

    fn help_to_no_add(&self) -> Self {
        match self {
            AnyTrackArg::Flag(f) => AnyTrackArg::Flag(f.help_to_no_add()),
            AnyTrackArg::Name(n) => AnyTrackArg::Name(n.help_to_no_add()),
        }
    }

    fn long(&self) -> &'static str {
        match self {
            AnyTrackArg::Flag(f) => f.long(),
            AnyTrackArg::Name(n) => n.long(),
        }
    }

    fn help(&self) -> &'static str {
        match self {
            AnyTrackArg::Flag(f) => f.help(),
            AnyTrackArg::Name(n) => n.help(),
        }
    }

    fn as_str(&self) -> &'static str {
        match self {
            AnyTrackArg::Flag(f) => TracksFlags::as_str(*f),
            AnyTrackArg::Name(n) => TracksNames::as_str(*n),
        }
    }
}

trait InverseBlockFactory {
    fn iter_help() -> impl Iterator<Item = Self>;
    fn help_to_add(&self) -> Self;
    fn help_to_no_add(&self) -> Self;
    fn long(&self) -> &'static str;
    fn help(&self) -> &'static str;
}

impl InverseBlockFactory for TracksFlagsArg {
    fn iter_help() -> impl Iterator<Item = Self> {
        [
            TracksFlagsArg::HelpAddDefaults,
            TracksFlagsArg::HelpAddForceds,
            TracksFlagsArg::HelpAddEnableds,
        ]
        .into_iter()
    }

    fn help_to_add(&self) -> Self {
        match self {
            TracksFlagsArg::HelpAddDefaults => TracksFlagsArg::AddDefaults,
            TracksFlagsArg::HelpAddForceds => TracksFlagsArg::AddForceds,
            TracksFlagsArg::HelpAddEnableds => TracksFlagsArg::AddEnableds,
            _ => panic!("Received unsupported Help arg"),
        }
    }

    fn help_to_no_add(&self) -> Self {
        match self {
            TracksFlagsArg::HelpAddDefaults => TracksFlagsArg::NoAddDefaults,
            TracksFlagsArg::HelpAddForceds => TracksFlagsArg::NoAddForceds,
            TracksFlagsArg::HelpAddEnableds => TracksFlagsArg::NoAddEnableds,
            _ => panic!("Received unsupported Help arg"),
        }
    }

    fn long(&self) -> &'static str {
        match self {
            TracksFlagsArg::HelpAddDefaults => "add-defaults / --no-add-defaults",
            TracksFlagsArg::AddDefaults => "add-defaults",
            TracksFlagsArg::NoAddDefaults => "no-add-defaults",
            TracksFlagsArg::HelpAddForceds => "add-forceds / --no-add-forceds",
            TracksFlagsArg::AddForceds => "add-forceds",
            TracksFlagsArg::NoAddForceds => "no-add-forceds",
            TracksFlagsArg::HelpAddEnableds => "add-enableds / --no-add-enableds",
            TracksFlagsArg::AddEnableds => "add-enableds",
            TracksFlagsArg::NoAddEnableds => "no-add-enableds",
            _ => panic!("Received not inverse arg"),
        }
    }

    fn help(&self) -> &'static str {
        match self {
            TracksFlagsArg::HelpAddDefaults => "On/Off auto set default-track-flags",
            TracksFlagsArg::HelpAddForceds => "On/Off auto set forced-display-flags",
            TracksFlagsArg::HelpAddEnableds => "On/Off auto set track-enabled-flags",
            _ => panic!("Received not Help inverse arg"),
        }
    }
}

impl InverseBlockFactory for TracksNamesArg {
    fn iter_help() -> impl Iterator<Item = Self> {
        [TracksNamesArg::HelpAddNames].into_iter()
    }

    fn help_to_add(&self) -> Self {
        match self {
            TracksNamesArg::HelpAddNames => TracksNamesArg::AddNames,
            _ => panic!("Received unsupported Help arg"),
        }
    }

    fn help_to_no_add(&self) -> Self {
        match self {
            TracksNamesArg::HelpAddNames => TracksNamesArg::NoAddNames,
            _ => panic!("Received unsupported Help arg"),
        }
    }

    fn long(&self) -> &'static str {
        match self {
            TracksNamesArg::HelpAddNames => "add-names / --no-add-names",
            TracksNamesArg::AddNames => "add-names",
            TracksNamesArg::NoAddNames => "no-add-names",
            _ => panic!("Received not inverse arg"),
        }
    }

    fn help(&self) -> &'static str {
        match self {
            TracksNamesArg::HelpAddNames => "On/Off auto set track-names",
            _ => panic!("Received not Help inverse arg"),
        }
    }
}
