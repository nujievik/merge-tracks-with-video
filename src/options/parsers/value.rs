use crate::Output;
use clap::builder::TypedValueParser;
use clap::error::{ContextKind, ContextValue, ErrorKind};
use globset::{Glob, GlobSet, GlobSetBuilder};
use std::ffi::OsStr;
use std::path::{Path, PathBuf};

#[derive(Clone)]
pub(in crate::options) struct StartDirParser;

impl TypedValueParser for StartDirParser {
    type Value = PathBuf;

    fn parse_ref(
        &self,
        cmd: &clap::Command,
        arg: Option<&clap::Arg>,
        value: &OsStr,
    ) -> Result<Self::Value, clap::Error> {
        self.validate(value).map_err(|msg| {
            let mut err = clap::Error::raw(ErrorKind::InvalidValue, msg);
            if let Some(arg) = arg {
                err.insert(
                    ContextKind::InvalidArg,
                    ContextValue::String(arg.get_id().to_string()),
                );
            }
            err.with_cmd(cmd)
        })
    }
}

impl StartDirParser {
    pub fn validate(&self, raw: &OsStr) -> Result<PathBuf, String> {
        let path = Path::new(raw);
        let path = std::fs::canonicalize(&path)
            .map_err(|e| format!("Invalid path: '{}': {}\n", path.display(), e.to_string()))?;

        if !path.is_dir() {
            return Err(format!("Path is not a directory: '{}'\n", path.display()));
        }

        match std::fs::read_dir(&path) {
            Ok(_) => Ok(path),
            Err(e) => Err(format!(
                "Directory '{}' is not readable: {}\n",
                path.display(),
                e
            )),
        }
    }
}

#[derive(Clone)]
pub(in crate::options) struct OutputParser;

impl TypedValueParser for OutputParser {
    type Value = Output;

    fn parse_ref(
        &self,
        cmd: &clap::Command,
        arg: Option<&clap::Arg>,
        value: &OsStr,
    ) -> Result<Self::Value, clap::Error> {
        Output::from_path(value).map_err(|msg| {
            let mut err = clap::Error::raw(ErrorKind::InvalidValue, msg);
            if let Some(arg) = arg {
                err.insert(
                    ContextKind::InvalidArg,
                    ContextValue::String(arg.get_id().to_string()),
                );
            }
            err.with_cmd(cmd)
        })
    }
}

pub(in crate::options) fn parse_patterns(s: &str) -> Result<GlobSet, String> {
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
