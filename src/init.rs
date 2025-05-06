use crate::types::{AppConfig, AppFlow, LangCode, RawAppConfig, Tool, ToolPkg, Tools};
use crate::unwrap_or_return;
use clap::{CommandFactory, FromArgMatches};
use std::ffi::OsString;

pub fn init() -> AppFlow<(AppConfig, Tools)> {
    let cfg = RawAppConfig::new();

    if cfg.list_langs {
        LangCode::print_list_langs();
        return AppFlow::Done;
    }

    if cfg.list_targets {
        // add call print_list_targets function
        return AppFlow::Done;
    }

    if let Some((tool, args)) = cfg.call_tool {
        unwrap_or_return!(try_call_tool(tool, args));
    }

    let cmd = AppConfig::command();
    let mut matches = cmd.get_matches_from(cfg.args);

    let cfg = AppConfig::from_arg_matches_mut(&mut matches);
    let cfg = unwrap_or_return!(AppFlow::from_result(cfg));

    cfg.verbosity.init_env_logger();

    AppFlow::Done
}

fn try_call_tool(tool: Tool, args: Vec<OsString>) -> AppFlow<()> {
    let tools = unwrap_or_return!(try_init_tools());
    match tools.execute(tool, args, None) {
        Ok(msg) => {
            println!("{}", msg);
            AppFlow::Done
        }
        Err(e) => AppFlow::Fail(e.into()),
    }
}

fn try_init_tools() -> AppFlow<Tools> {
    let tools = Tools::new();
    match tools.check_pkg(ToolPkg::Mkvtoolnix) {
        Ok(_) => AppFlow::Proceed(tools),
        Err(e) => AppFlow::from(e),
    }
}

/*
l e*t matches = unwrap_or_return!(try_get_matches_from(cfg.args));

let verbosity = from_matches::verbosity(&matches);
let locale = from_matches::locale(&matches);

unwrap_or_return!(crate::i18n::try_init(&verbosity, &locale));

if let Some((tool, args)) = cfg.call_tool {
    unwrap_or_return!(call_tool(tool, args));
    }

    let cfg = unwrap_or_return!(AppConfig::from_matches(matches, verbosity, locale));
    let tools = unwrap_or_return!(try_init_tools());

    AppFlow::Proceed((cfg, tools))
    */

/*
fn try_get_matches_from(args: Vec<OsString>) -> AppFlow<ArgMatches> {
    match cmd_clap::new().try_get_matches_from(args) {
        Ok(m) => AppFlow::Proceed(m),
        Err(e) => {
            if let Err(print_err) = e.print() {
                eprintln!("Crit Err: fail print {}", print_err);
                return AppFlow::Fail(1);
            }

            if e.use_stderr() {
                AppFlow::Fail(2)
            } else {
                AppFlow::Done
            }
        }
    }
}
*/
