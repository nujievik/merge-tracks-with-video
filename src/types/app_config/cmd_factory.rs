mod global;
mod inverse;
mod io;
mod other;
mod retiming;
mod target;
mod val_parsers;

use super::AppConfig;
use clap::Command;

impl clap::CommandFactory for AppConfig {
    fn command() -> Command {
        Blocks::new()
            .io()
            .global()
            .inverse()
            .retiming()
            .target()
            .other()
            .version()
            .help()
            .unwrap()
    }

    fn command_for_update() -> Command {
        Self::command()
    }
}

struct Blocks {
    cmd: Command,
}

impl Blocks {
    // other fn impl Blocks in modules
    fn new() -> Self {
        Self {
            cmd: Command::new(env!("CARGO_PKG_NAME"))
                .no_binary_name(true)
                .version(concat!("v", env!("CARGO_PKG_VERSION")))
                .disable_help_flag(true)
                .disable_version_flag(true)
                .override_usage(concat!(env!("CARGO_PKG_NAME"), " [options]")),
        }
    }

    fn unwrap(self) -> Command {
        self.cmd
    }
}
