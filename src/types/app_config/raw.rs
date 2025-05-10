#[cfg(test)]
mod tests;

use crate::traits::TryInit;
use crate::types::{AppError, LangCode, Target, TargetGroup, Tool, Tools};
use std::collections::HashMap;
use std::ffi::OsString;
use std::path::PathBuf;

pub struct RawAppConfig {
    pub list_langs: bool,
    pub list_targets: bool,
    pub call_tool: Option<(Tool, Vec<OsString>)>,
    pub args: Vec<OsString>,
    pub trg_args: Option<HashMap<Target, Vec<OsString>>>,
}

impl TryInit for RawAppConfig {
    fn try_init() -> Result<Self, AppError> {
        let args: Vec<OsString> = std::env::args_os().skip(1).collect();
        let cfg = Self::new_from_args(args)?;

        if cfg.list_langs {
            LangCode::print_list_langs();
            return Err(AppError::ok());
        }

        if cfg.list_targets {
            // add fn print_list_targets()
            return Err(AppError::ok());
        }

        if let Some((tool, args)) = cfg.call_tool {
            let tools = Tools::new().try_set_paths([tool])?;
            let msg = tools.execute(&tool, args, None)?;
            println!("{}", msg);
            return Err(AppError::ok());
        }

        Ok(cfg)
    }
}

impl RawAppConfig {
    fn parse_target(arg: &OsString) -> Result<Target, AppError> {
        let s = arg.to_string_lossy();
        let target = if let Ok(group) = s.parse::<TargetGroup>() {
            Target::Group(group)
        } else {
            let path = PathBuf::from(arg.clone())
                .canonicalize()
                .map_err(|e| AppError::from(format!("Incorrect path target '{}': {}", s, e)));
            Target::Path(path?)
        };

        Ok(target)
    }

    fn new_from_args(in_args: Vec<OsString>) -> Result<Self, AppError> {
        let mut list_langs = false;
        let mut list_targets = false;
        let mut call_tool: Option<(Tool, Vec<OsString>)> = None;
        let mut args: Vec<OsString> = Vec::new();
        let mut trg_args: Option<HashMap<Target, Vec<OsString>>> = None;
        let mut current_target: Option<Target> = None;

        let mut iter = in_args.into_iter();

        while let Some(arg) = iter.next() {
            let s = arg.to_string_lossy();

            if s == "--list-langs" || s == "--list-languages" {
                list_langs = true;
                break;
            }

            if s == "--list-targets" {
                list_targets = true;
                break;
            }

            if s.starts_with("--") {
                let maybe_tool = &s[2..];
                if let Ok(tool) = maybe_tool.parse::<Tool>() {
                    let remaining_args: Vec<OsString> = iter.collect();
                    call_tool = Some((tool, remaining_args));
                    break;
                }
            }

            match s.as_ref() {
                "--target" | "-t" => {
                    if let Some(trg_arg) = iter.next() {
                        let trg_str = trg_arg.to_string_lossy();
                        if trg_str == "global" || trg_str == "g" {
                            current_target = None;
                        } else {
                            let target = Self::parse_target(&trg_arg)?;
                            current_target = Some(target.clone());

                            trg_args
                                .get_or_insert_with(HashMap::new)
                                .entry(target)
                                .or_insert_with(Vec::new);
                        }
                    }
                }
                _ => {
                    if let Some(target) = &current_target {
                        if let Some(map) = trg_args.as_mut() {
                            map.get_mut(target).unwrap().push(arg);
                        }
                    } else {
                        args.push(arg);
                    }
                }
            }
        }

        Ok(Self {
            list_langs,
            list_targets,
            call_tool,
            args,
            trg_args,
        })
    }
}
