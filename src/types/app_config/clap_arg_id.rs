use super::AppConfig;
use crate::types::traits::ClapArgID;

pub(in crate::types) enum AppConfigArg {
    Locale,
    ExitOnErr,
    Pro,
}

impl ClapArgID for AppConfig {
    type Arg = AppConfigArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            AppConfigArg::Locale => "locale",
            AppConfigArg::ExitOnErr => "exit_on_err",
            AppConfigArg::Pro => "pro",
        }
    }
}
