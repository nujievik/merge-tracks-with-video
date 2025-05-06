use super::Blocks;
use clap::{Arg, ArgAction};

impl Blocks {
    pub fn other(mut self) -> Self {
        // Help Only. This args processing in crate::types::app_config::raw
        self.cmd = self
            .cmd
            .next_help_heading("Other options")
            .arg(
                Arg::new("list_langs")
                    .long("list-langs")
                    .help("Show supported language codes")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new("ffprobe_help")
                    .long("ffprobe [options]")
                    .help("Call ffprobe")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new("mkvextract")
                    .long("mkvextract [options]")
                    .help("Call mkvextract")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new("mkvinfo_help")
                    .long("mkvinfo [options]")
                    .help("Call mkvinfo")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new("mkvmerge_help")
                    .long("mkvmerge [options]")
                    .help("Call mkvmerge")
                    .action(ArgAction::SetTrue),
            );

        self
    }

    pub fn version(mut self) -> Self {
        self.cmd = self.cmd.arg(
            Arg::new("version")
                .short('V')
                .long("version")
                .help_heading("Other options")
                .help("Show version")
                .action(ArgAction::Version),
        );

        self
    }

    pub fn help(mut self) -> Self {
        self.cmd = self.cmd.arg(
            Arg::new("help")
                .short('h')
                .long("help")
                .help_heading("Other options")
                .help("Show help")
                .action(ArgAction::Help),
        );

        self
    }
}
