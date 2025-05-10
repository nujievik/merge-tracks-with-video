pub(in crate::types) mod from_arg_matches;
mod topmost;

use crate::types::RangeU32;
use globset::GlobSet;
use std::path::PathBuf;

pub struct Input {
    pub dir: PathBuf,
    pub range: RangeU32,
    pub up: u32,
    pub check: u32,
    pub skip: Option<GlobSet>,
    pub topmost: Option<PathBuf>,
}

impl Input {
    pub fn normalize_dir(dir: impl Into<PathBuf>) -> Result<PathBuf, std::io::Error> {
        let dir = std::fs::canonicalize(dir.into())?;
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
