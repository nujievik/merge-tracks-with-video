use crate::types::RangeU32;
use crate::types::traits::ClapArgID;
use clap::{ArgMatches, Error, error::ErrorKind};
use globset::GlobSet;
use std::path::{Path, PathBuf};

pub struct Input {
    dir: PathBuf,
    range: RangeU32,
    up: u32,
    check: u32,
    skip: Option<GlobSet>,
}

impl Input {
    pub fn get_dir(&self) -> PathBuf {
        self.dir.clone()
    }

    pub fn get_range(&self) -> RangeU32 {
        self.range
    }

    pub fn get_up(&self) -> u32 {
        self.up
    }

    pub fn get_check(&self) -> u32 {
        self.check
    }

    pub fn get_skip(&self) -> Option<GlobSet> {
        self.skip.clone()
    }

    pub fn normalize_dir(dir: impl AsRef<Path>) -> Result<PathBuf, std::io::Error> {
        let dir = std::fs::canonicalize(dir)?;
        std::fs::read_dir(&dir)?;
        Ok(dir)
    }

    fn default_dir() -> Result<PathBuf, std::io::Error> {
        Self::normalize_dir(".")
    }

    fn default_range() -> RangeU32 {
        RangeU32::new().start(0).end(u32::MAX)
    }

    fn default_up() -> u32 {
        8
    }

    fn default_check() -> u32 {
        128
    }
}

pub(in crate::types) enum InputArg {
    Dir,
    Range,
    Up,
    Check,
    Skip,
}

impl ClapArgID for Input {
    type Arg = InputArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            InputArg::Dir => "input",
            InputArg::Range => "range",
            InputArg::Up => "up",
            InputArg::Check => "check",
            InputArg::Skip => "skip",
        }
    }
}

impl clap::FromArgMatches for Input {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let dir = match matches
            .try_remove_one::<PathBuf>(Self::as_str(InputArg::Dir))
            .map_err(|e| Error::raw(ErrorKind::InvalidValue, e.to_string()))?
        {
            Some(path) => path,
            None => Self::default_dir()
                .map_err(|e| Error::raw(ErrorKind::ValueValidation, e.to_string()))?,
        };

        let range = match matches
            .try_remove_one::<RangeU32>(Self::as_str(InputArg::Range))
            .map_err(|e| Error::raw(ErrorKind::ValueValidation, e.to_string()))?
        {
            Some(rng) => rng,
            None => Self::default_range(),
        };

        let up = match matches
            .try_remove_one::<u32>(Self::as_str(InputArg::Up))
            .map_err(|e| Error::raw(ErrorKind::ValueValidation, e.to_string()))?
        {
            Some(u) => u,
            None => Self::default_up(),
        };

        let check = match matches
            .try_remove_one::<u32>(Self::as_str(InputArg::Check))
            .map_err(|e| Error::raw(ErrorKind::ValueValidation, e.to_string()))?
        {
            Some(u) => u,
            None => Self::default_check(),
        };

        let skip = matches
            .try_remove_one::<GlobSet>(Self::as_str(InputArg::Skip))
            .map_err(|e| Error::raw(ErrorKind::ValueValidation, e.to_string()))?;

        Ok(Self {
            dir,
            range,
            up,
            check,
            skip,
        })
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
