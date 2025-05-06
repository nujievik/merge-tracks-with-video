use super::Blocks;

use super::val_parsers::ChaptersParser;
use crate::types::attachs::{Attachs, BaseAttachsFields, from_arg_matches::AttachsArg};
use crate::types::chapters::{Chapters, ChaptersArg};
use crate::types::tracks::{BaseTracksFields, BaseTracksFlagsFields, Tracks, TracksFlags};
use crate::types::tracks::{TracksNames, names::from_arg_matches::TracksNamesArg};
use crate::types::tracks::{flags::from_arg_matches::TracksFlagsArg, from_arg_matches::TracksArg};
use crate::types::traits::ClapArgID;
use clap::{Arg, ArgAction, builder::ValueParser};
use std::str::FromStr;

impl Blocks {
    pub fn target(mut self) -> Self {
        self.cmd = self
            .cmd
            .next_help_heading("Target options")
            .arg(
                Arg::new("target_help")
                    .short('t')
                    .long("target <trg> [options]")
                    .help("Set next options for target")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new("list_targets")
                    .long("list-targets")
                    .help("Show supported targets")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new("target_exclude_help")
                    .long("target <trg> --no-files")
                    .help("Exclude trg files (no global trg)")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new(Tracks::as_str(TracksArg::Audio))
                    .short('a')
                    .long("audio")
                    .aliases(&["audio-tracks", "atracks"])
                    .value_name("[!]n[,m]...")
                    .help("[!]Copy audio tracks n,m etc.")
                    .value_parser(ValueParser::new(BaseTracksFields::from_str)),
            )
            .arg(
                Arg::new(Tracks::as_str(TracksArg::NoAudio))
                    .short('A')
                    .long("no-audio")
                    .alias("noaudio")
                    .help("Don't copy any audio track")
                    .action(ArgAction::SetTrue)
                    .conflicts_with(Tracks::as_str(TracksArg::Audio)),
            )
            .arg(
                Arg::new(Tracks::as_str(TracksArg::Video))
                    .short('d')
                    .long("video")
                    .aliases(&["video-tracks", "vtracks"])
                    .value_name("[!]n[,m]...")
                    .help("[!]Copy video tracks n,m etc.")
                    .value_parser(ValueParser::new(BaseTracksFields::from_str)),
            )
            .arg(
                Arg::new(Tracks::as_str(TracksArg::NoVideo))
                    .short('D')
                    .long("no-video")
                    .alias("novideo")
                    .help("Don't copy any video track")
                    .action(ArgAction::SetTrue)
                    .conflicts_with(Tracks::as_str(TracksArg::Video)),
            )
            .arg(
                Arg::new(Tracks::as_str(TracksArg::Subs))
                    .short('s')
                    .long("subs")
                    .aliases(&["subtitle-tracks", "subtitles", "sub-tracks", "stracks"])
                    .value_name("[!]n[,m]...")
                    .help("[!]Copy subtitle tracks n,m etc.")
                    .value_parser(ValueParser::new(BaseTracksFields::from_str)),
            )
            .arg(
                Arg::new(Tracks::as_str(TracksArg::NoSubs))
                    .short('S')
                    .long("no-subs")
                    .aliases(&["no-subtitles", "nosubs"])
                    .help("Don't copy any subtitle track")
                    .action(ArgAction::SetTrue)
                    .conflicts_with(Tracks::as_str(TracksArg::Subs)),
            )
            .arg(
                Arg::new(Tracks::as_str(TracksArg::Buttons))
                    .short('b')
                    .long("buttons")
                    .aliases(&["button-tracks", "btracks"])
                    .value_name("[!]n[,m]...")
                    .help("[!]Copy button tracks n,m etc.")
                    .value_parser(ValueParser::new(BaseTracksFields::from_str)),
            )
            .arg(
                Arg::new(Tracks::as_str(TracksArg::NoButtons))
                    .short('B')
                    .long("no-buttons")
                    .alias("nobuttons")
                    .help("Don't copy any button track")
                    .action(ArgAction::SetTrue)
                    .conflicts_with(Tracks::as_str(TracksArg::Buttons)),
            )
            .arg(
                Arg::new(Chapters::as_str(ChaptersArg::Chapters))
                    .short('c')
                    .long("chapters")
                    .value_name("chp")
                    .help("Chapters info from chp file")
                    .value_parser(ValueParser::new(ChaptersParser)),
            )
            .arg(
                Arg::new(Chapters::as_str(ChaptersArg::NoChapters))
                    .short('C')
                    .long("no-chapters")
                    .help("Don't keep chapters")
                    .action(ArgAction::SetTrue)
                    .conflicts_with(Chapters::as_str(ChaptersArg::Chapters)),
            )
            .arg(
                Arg::new(Attachs::as_str(AttachsArg::Attachs))
                    .short('m')
                    .long("attachs")
                    .alias("attachments")
                    .value_name("[!]n[,m]...")
                    .help("[!]Copy attachments n,m etc.")
                    .value_parser(ValueParser::new(BaseAttachsFields::from_str)),
            )
            .arg(
                Arg::new(Attachs::as_str(AttachsArg::NoAttachs))
                    .short('M')
                    .long("no-attachs")
                    .aliases(&["no-attachments", "noattachments", "noattachs"])
                    .help("Don't copy any attachment")
                    .action(ArgAction::SetTrue)
                    .conflicts_with(Attachs::as_str(AttachsArg::Attachs)),
            )
            .arg(
                Arg::new(Attachs::as_str(AttachsArg::Fonts))
                    .short('f')
                    .long("fonts")
                    .value_name("[!]n[,m]...")
                    .help("[!]Copy fonts n,m etc.")
                    .value_parser(ValueParser::new(BaseAttachsFields::from_str)),
            )
            .arg(
                Arg::new(Attachs::as_str(AttachsArg::NoFonts))
                    .short('F')
                    .long("no-fonts")
                    .alias("nofonts")
                    .help("Don't copy any font")
                    .action(ArgAction::SetTrue)
                    .conflicts_with(Attachs::as_str(AttachsArg::Fonts)),
            )
            .arg(
                Arg::new(TracksFlags::as_str(TracksFlagsArg::Defaults))
                    .long("defaults")
                    .aliases(&["default-track-flag", "default-track"])
                    .value_name("[n:]B[,m:B]...")
                    .help("Bool value default-track-flag's")
                    .value_parser(ValueParser::new(BaseTracksFlagsFields::from_str)),
            )
            .arg(
                Arg::new(TracksFlags::as_str(TracksFlagsArg::LimDefaults))
                    .long("lim-defaults")
                    .value_name("n")
                    .help("Max true default-track-flag's in auto")
                    .value_parser(clap::value_parser!(u32)),
            )
            .arg(
                Arg::new(TracksFlags::as_str(TracksFlagsArg::Forceds))
                    .long("forceds")
                    .aliases(&["forced-display-flag", "forced-track"])
                    .value_name("[n:]B[,m:B]...")
                    .help("Bool forced-display-flag")
                    .value_parser(ValueParser::new(BaseTracksFlagsFields::from_str)),
            )
            .arg(
                Arg::new(TracksFlags::as_str(TracksFlagsArg::LimForceds))
                    .long("lim-forceds")
                    .value_name("n")
                    .help("Max true forced-display-flag's in auto")
                    .value_parser(clap::value_parser!(u32)),
            )
            .arg(
                Arg::new(TracksFlags::as_str(TracksFlagsArg::Enableds))
                    .long("enableds")
                    .alias("track-enabled-flag")
                    .value_name("[n:]B[,m:B]...")
                    .help("Bool track-enabled-flag")
                    .value_parser(ValueParser::new(BaseTracksFlagsFields::from_str)),
            )
            .arg(
                Arg::new(TracksFlags::as_str(TracksFlagsArg::LimEnableds))
                    .long("lim-enableds")
                    .value_name("n")
                    .help("Max true track-enabled-flag's in auto")
                    .value_parser(clap::value_parser!(u32)),
            )
            .arg(
                Arg::new(TracksNames::as_str(TracksNamesArg::Names))
                    .long("names")
                    .aliases(&["track-names", "track-name"])
                    .value_name("[n:]N[,m:N]...")
                    .help("Track names"),
            );
        /*
        .arg(
            Arg::new("language")
            .long("lang")
            .alias("language")
            .value_name("L or n:L[,m:L]...")
            .help("Track language"),
        )
        .arg(
            Arg::new("specials")
            .long("specials")
            .value_name("spl")
            .help("Set unpresented mkvmerge options"),
        )
        */

        self
    }
}
