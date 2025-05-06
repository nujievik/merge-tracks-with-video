use crate::types::traits::ClapArgID;
use clap::{ArgMatches, Error, error::ErrorKind};
use std::fs::{File, canonicalize};
use std::path::{Path, PathBuf};

#[derive(Clone)]
pub struct Chapters {
    pub no_flag: bool,
    pub file: Option<PathBuf>,
}

impl Chapters {
    pub fn from_path(path: impl AsRef<Path>) -> Result<Self, std::io::Error> {
        let path = canonicalize(path)?;
        if !path.is_file() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::IsADirectory,
                "Is not a file",
            ));
        }
        File::open(&path)?;

        Ok(Self {
            no_flag: Self::default_no_flag(),
            file: Some(path),
        })
    }

    fn new() -> Self {
        Self {
            no_flag: false,
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

pub(in crate::types) enum ChaptersArg {
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
        let no_flag = match matches
            .try_remove_one::<bool>(Chapters::as_str(ChaptersArg::NoChapters))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(b) => b,
            None => Self::default_no_flag(),
        };

        let chapters = if no_flag {
            Chapters::new().no_flag(true)
        } else {
            match matches
                .try_remove_one::<Self>(Chapters::as_str(ChaptersArg::Chapters))
                .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
            {
                Some(chp) => chp,
                None => Chapters::new(),
            }
        };

        Ok(chapters)
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), clap::Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
