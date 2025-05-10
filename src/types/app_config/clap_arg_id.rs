use super::AppConfig;
use crate::traits::ClapArgID;

pub enum AppConfigArg {
    Lim,
    Output,
    Locale,
    ExitOnErr,
    Pro,
}

impl ClapArgID for AppConfig {
    type Arg = AppConfigArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            AppConfigArg::Lim => "lim",
            AppConfigArg::Output => "output",
            AppConfigArg::Locale => "locale",
            AppConfigArg::ExitOnErr => "exit_on_err",
            AppConfigArg::Pro => "pro",
        }
    }
}
