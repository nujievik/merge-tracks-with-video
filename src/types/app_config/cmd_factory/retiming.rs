use super::Blocks;

use super::val_parsers::patterns_parser;
use crate::types::retiming::{Retiming, RetimingArg};
use crate::types::traits::ClapArgID;
use clap::{Arg, ArgAction, builder::ValueParser};

impl Blocks {
    pub fn retiming(mut self) -> Self {
        self.cmd = self
            .cmd
            .next_help_heading("Retiming options")
            .arg(
                Arg::new(Retiming::as_str(RetimingArg::RmSegments))
                    .long("rm-segments")
                    .alias("remove-segments")
                    .value_name("n[,m]...")
                    .help("Remove segments with name patterns")
                    .value_parser(ValueParser::new(patterns_parser)),
            )
            .arg(
                Arg::new(Retiming::as_str(RetimingArg::NoLinked))
                    .long("no-linked")
                    .help("Remove linked segments")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new(Retiming::as_str(RetimingArg::Less))
                    .long("less-retiming")
                    .help("No retiming if linked segments outside main")
                    .action(ArgAction::SetTrue),
            );

        self
    }
}
