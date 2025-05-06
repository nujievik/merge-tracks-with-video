use super::Blocks;
use super::val_parsers::{InputDirParser, OutputParser, patterns_parser};
use crate::types::RangeU32;
use crate::types::input::{Input, InputArg};
use crate::types::output::{Output, OutputArg};
use crate::types::traits::ClapArgID;
use clap::{Arg, builder::ValueParser};
use std::str::FromStr;

impl Blocks {
    pub fn io(mut self) -> Self {
        self.cmd = self
            .cmd
            .next_help_heading("I/O options")
            .arg(
                Arg::new(Input::as_str(InputArg::Dir))
                    .short('i')
                    .long("input")
                    .aliases(&["start-directory", "start-dir"])
                    .value_name("dir")
                    .help("File search start directory")
                    .value_parser(ValueParser::new(InputDirParser)),
            )
            .arg(
                Arg::new(Output::as_str(OutputArg::Out))
                    .short('o')
                    .long("output")
                    .value_name("out[,put]")
                    .help("Output paths pattern: out{num}[put]")
                    .value_parser(ValueParser::new(OutputParser)),
            )
            .arg(
                Arg::new(Input::as_str(InputArg::Range))
                    .short('r')
                    .long("range")
                    .alias("range-mux")
                    .value_name("n[-m]")
                    .help("Number range of file names to mux")
                    .value_parser(ValueParser::new(RangeU32::from_str)),
            )
            .arg(
                Arg::new(Output::as_str(OutputArg::Lim))
                    .long("lim")
                    .aliases(&["limit-mux", "lim-mux", "limit"])
                    .value_name("n")
                    .help("Max number of muxed files to create")
                    .value_parser(clap::value_parser!(u32).range(1..)),
            )
            .arg(
                Arg::new(Input::as_str(InputArg::Up))
                    .long("up")
                    .aliases(&["lim-upward", "lim-up", "upward"])
                    .value_name("n")
                    .help("Max directory levels to search upward")
                    .value_parser(clap::value_parser!(u32)),
            )
            .arg(
                Arg::new(Input::as_str(InputArg::Check))
                    .long("check")
                    .alias("lim-check")
                    .value_name("n")
                    .help("Max files to check per directory level")
                    .value_parser(clap::value_parser!(u32).range(1..)),
            )
            .arg(
                Arg::new(Input::as_str(InputArg::Skip))
                    .long("skip")
                    .value_name("n[,m]...")
                    .help("Skip media with path patterns")
                    .value_parser(ValueParser::new(patterns_parser)),
            );

        self
    }
}
