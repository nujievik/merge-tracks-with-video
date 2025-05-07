use super::super::{AppConfig, clap_arg_id::AppConfigArg};
use super::Blocks;
use crate::types::LangCode;
use crate::types::traits::ClapArgID;
use crate::types::verbosity::{Verbosity, VerbosityArg};
use clap::{Arg, ArgAction, builder::ValueParser};
use std::str::FromStr;

impl Blocks {
    pub fn global(mut self) -> Self {
        self.cmd = self
            .cmd
            .next_help_heading("Global options")
            .arg(
                Arg::new(Verbosity::as_str(VerbosityArg::Verbose))
                    .short('v')
                    .long("verbose")
                    .help("Increase verbosity")
                    .action(ArgAction::Count),
            )
            .arg(
                Arg::new(Verbosity::as_str(VerbosityArg::Quiet))
                    .short('q')
                    .long("quiet")
                    .help("Suppress logging")
                    .action(ArgAction::SetTrue)
                    .conflicts_with(Verbosity::as_str(VerbosityArg::Verbose)),
            )
            .arg(
                Arg::new(AppConfig::as_str(AppConfigArg::Locale))
                    .short('l')
                    .long("locale")
                    .value_name("lng")
                    .help("Locale language (on logging and sort)")
                    .value_parser(ValueParser::new(LangCode::from_str)),
            )
            .arg(
                Arg::new(AppConfig::as_str(AppConfigArg::ExitOnErr))
                    .short('e')
                    .long("exit-on-err")
                    .alias("exit-on-error")
                    .help("Skip mux for next files if err")
                    .action(ArgAction::SetTrue),
            )
            .arg(
                Arg::new(AppConfig::as_str(AppConfigArg::Pro))
                    .short('p')
                    .long("pro")
                    .alias("pro-mode")
                    .help("Off all auto 'Off on Pro options'")
                    .action(ArgAction::SetTrue),
            );

        self
    }
}
