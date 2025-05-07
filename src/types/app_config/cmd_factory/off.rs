use super::Blocks;
use crate::types::attachs::{Attachs, from_arg_matches::AttachsArg};
use crate::types::tracks::{
    TracksFlags, TracksLangs, TracksNames, flags::from_arg_matches::TracksFlagsArg,
    langs::from_arg_matches::TracksLangsArg, names::from_arg_matches::TracksNamesArg,
};
use crate::types::traits::ClapArgID;
use clap::{Arg, ArgAction};

impl Blocks {
    pub fn off(mut self) -> Self {
        let mut cmd = self.cmd.next_help_heading("Off on Pro options");

        for help in TracksFlagsArg::iter_help()
            .map(AnyOffArg::Flag)
            .chain(TracksNamesArg::iter_help().map(AnyOffArg::Name))
            .chain(TracksLangsArg::iter_help().map(AnyOffArg::Lang))
            .chain(AttachsArg::iter_help().map(AnyOffArg::Sort))
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

enum AnyOffArg {
    Flag(TracksFlagsArg),
    Name(TracksNamesArg),
    Lang(TracksLangsArg),
    Sort(AttachsArg),
}

impl AnyOffArg {
    fn help_to_add(&self) -> Self {
        match self {
            AnyOffArg::Flag(x) => AnyOffArg::Flag(x.help_to_add()),
            AnyOffArg::Name(x) => AnyOffArg::Name(x.help_to_add()),
            AnyOffArg::Lang(x) => AnyOffArg::Lang(x.help_to_add()),
            AnyOffArg::Sort(x) => AnyOffArg::Sort(x.help_to_add()),
        }
    }

    fn help_to_no_add(&self) -> Self {
        match self {
            AnyOffArg::Flag(x) => AnyOffArg::Flag(x.help_to_no_add()),
            AnyOffArg::Name(x) => AnyOffArg::Name(x.help_to_no_add()),
            AnyOffArg::Lang(x) => AnyOffArg::Lang(x.help_to_no_add()),
            AnyOffArg::Sort(x) => AnyOffArg::Sort(x.help_to_no_add()),
        }
    }

    fn long(&self) -> &'static str {
        match self {
            AnyOffArg::Flag(x) => x.long(),
            AnyOffArg::Name(x) => x.long(),
            AnyOffArg::Lang(x) => x.long(),
            AnyOffArg::Sort(x) => x.long(),
        }
    }

    fn help(&self) -> &'static str {
        match self {
            AnyOffArg::Flag(x) => x.help(),
            AnyOffArg::Name(x) => x.help(),
            AnyOffArg::Lang(x) => x.help(),
            AnyOffArg::Sort(x) => x.help(),
        }
    }

    fn as_str(&self) -> &'static str {
        match self {
            AnyOffArg::Flag(x) => TracksFlags::as_str(*x),
            AnyOffArg::Name(x) => TracksNames::as_str(*x),
            AnyOffArg::Lang(x) => TracksLangs::as_str(*x),
            AnyOffArg::Sort(x) => Attachs::as_str(*x),
        }
    }
}

trait OffBlockFactory {
    fn iter_help() -> impl Iterator<Item = Self>;
    fn help_to_add(&self) -> Self;
    fn help_to_no_add(&self) -> Self;
    fn long(&self) -> &'static str;
    fn help(&self) -> &'static str;
}

impl OffBlockFactory for TracksFlagsArg {
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

impl OffBlockFactory for TracksNamesArg {
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

impl OffBlockFactory for TracksLangsArg {
    fn iter_help() -> impl Iterator<Item = Self> {
        [TracksLangsArg::HelpAddLangs].into_iter()
    }

    fn help_to_add(&self) -> Self {
        match self {
            TracksLangsArg::HelpAddLangs => TracksLangsArg::AddLangs,
            _ => panic!("Received unsupported Help arg"),
        }
    }

    fn help_to_no_add(&self) -> Self {
        match self {
            TracksLangsArg::HelpAddLangs => TracksLangsArg::NoAddLangs,
            _ => panic!("Received unsupported Help arg"),
        }
    }

    fn long(&self) -> &'static str {
        match self {
            TracksLangsArg::HelpAddLangs => "add-langs / --no-add-langs",
            TracksLangsArg::AddLangs => "add-langs",
            TracksLangsArg::NoAddLangs => "no-add-langs",
            _ => panic!("Received not inverse arg"),
        }
    }

    fn help(&self) -> &'static str {
        match self {
            TracksLangsArg::HelpAddLangs => "On/Off auto set track-languages",
            _ => panic!("Received not Help inverse arg"),
        }
    }
}

impl OffBlockFactory for AttachsArg {
    fn iter_help() -> impl Iterator<Item = Self> {
        [AttachsArg::HelpSortFonts].into_iter()
    }

    fn help_to_add(&self) -> Self {
        match self {
            AttachsArg::HelpSortFonts => AttachsArg::SortFonts,
            _ => panic!("Received unsupported Help arg"),
        }
    }

    fn help_to_no_add(&self) -> Self {
        match self {
            AttachsArg::HelpSortFonts => AttachsArg::NoSortFonts,
            _ => panic!("Received unsupported Help arg"),
        }
    }

    fn long(&self) -> &'static str {
        match self {
            AttachsArg::HelpSortFonts => "sort-fonts / --no-sort-fonts",
            AttachsArg::SortFonts => "sort-fonts",
            AttachsArg::NoSortFonts => "no-sort-fonts",
            _ => panic!("Received not inverse arg"),
        }
    }

    fn help(&self) -> &'static str {
        match self {
            AttachsArg::HelpSortFonts => "On/Off sort in-files fonts",
            _ => panic!("Received not Help inverse arg"),
        }
    }
}
