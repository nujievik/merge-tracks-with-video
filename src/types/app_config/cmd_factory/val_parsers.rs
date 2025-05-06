use crate::types::{Chapters, Input, Output};
use clap::builder::TypedValueParser;
use clap::error::{ContextKind, ContextValue, ErrorKind};
use clap::{Arg, Command, Error};
use globset::{Glob, GlobSet, GlobSetBuilder};
use std::ffi::OsStr;
use std::path::PathBuf;

#[derive(Clone)]
pub(super) struct InputDirParser;

impl TypedValueParser for InputDirParser {
    type Value = PathBuf;

    fn parse_ref(
        &self,
        cmd: &Command,
        arg: Option<&Arg>,
        value: &OsStr,
    ) -> Result<Self::Value, Error> {
        Input::normalize_dir(value).map_err(|e| {
            let mut err = Error::new(ErrorKind::InvalidValue).with_cmd(&cmd);

            if let Some(arg) = arg {
                err.insert(
                    ContextKind::InvalidArg,
                    ContextValue::String(arg.to_string()),
                );
            }
            err.insert(
                ContextKind::InvalidValue,
                ContextValue::String(format!("{} (reason: {})", value.to_string_lossy(), e)),
            );

            err
        })
    }
}

#[derive(Clone)]
pub(super) struct OutputParser;

impl TypedValueParser for OutputParser {
    type Value = Output;

    fn parse_ref(
        &self,
        cmd: &Command,
        arg: Option<&Arg>,
        value: &OsStr,
    ) -> Result<Self::Value, Error> {
        Output::from_path(value).map_err(|e| {
            let mut err = Error::new(ErrorKind::InvalidValue).with_cmd(&cmd);

            if let Some(arg) = arg {
                err.insert(
                    ContextKind::InvalidArg,
                    ContextValue::String(arg.to_string()),
                );
            }
            err.insert(
                ContextKind::InvalidValue,
                ContextValue::String(format!("{} (reason: {})", value.to_string_lossy(), e)),
            );

            err
        })
    }
}

#[derive(Clone)]
pub(super) struct ChaptersParser;

impl TypedValueParser for ChaptersParser {
    type Value = Chapters;

    fn parse_ref(
        &self,
        cmd: &Command,
        arg: Option<&Arg>,
        value: &OsStr,
    ) -> Result<Self::Value, Error> {
        Chapters::from_path(value).map_err(|e| {
            let mut err = Error::new(ErrorKind::InvalidValue).with_cmd(&cmd);

            if let Some(arg) = arg {
                err.insert(
                    ContextKind::InvalidArg,
                    ContextValue::String(arg.to_string()),
                );
            }
            err.insert(
                ContextKind::InvalidValue,
                ContextValue::String(format!("{} (reason: {})", value.to_string_lossy(), e)),
            );

            err
        })
    }
}

pub(super) fn patterns_parser(s: &str) -> Result<GlobSet, String> {
    let mut builder = GlobSetBuilder::new();

    for pattern in s.split(',') {
        let glob =
            Glob::new(pattern).map_err(|e| format!("Invalid pattern '{}': {}", pattern, e))?;
        builder.add(glob);
    }

    builder
        .build()
        .map_err(|e| format!("Failed to build patterns: {}", e))
}
