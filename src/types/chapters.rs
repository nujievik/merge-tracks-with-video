use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error};
use std::path::PathBuf;

#[derive(Clone)]
pub struct Chapters {
    pub no_flag: bool,
    pub file: Option<PathBuf>,
}

impl Chapters {
    pub fn from_path(path: impl Into<PathBuf>) -> Result<Self, std::io::Error> {
        let path = std::fs::canonicalize(path.into())?;
        if !path.is_file() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::IsADirectory,
                "Is not a file",
            ));
        }
        std::fs::File::open(&path)?;

        Ok(Self {
            no_flag: Self::default_no_flag(),
            file: Some(path),
        })
    }

    fn new() -> Self {
        Self {
            no_flag: Self::default_no_flag(),
            file: None,
        }
    }

    fn no_flag(mut self, no_flag: bool) -> Self {
        self.no_flag = no_flag;
        self
    }

    fn default_no_flag() -> bool {
        false
    }
}

pub enum ChaptersArg {
    NoChapters,
    Chapters,
}

impl ClapArgID for Chapters {
    type Arg = ChaptersArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            ChaptersArg::NoChapters => "no_chapters",
            ChaptersArg::Chapters => "chapters",
        }
    }
}

impl clap::FromArgMatches for Chapters {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let no_flag = val_from_matches!(
            matches,
            bool,
            ChaptersArg::NoChapters,
            Self::default_no_flag
        );

        Ok(if no_flag {
            Chapters::new().no_flag(true)
        } else {
            val_from_matches!(matches, Self, ChaptersArg::Chapters, Self::new)
        })
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), clap::Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
