mod from_path_helpers;

use crate::types::traits::ClapArgID;
use std::ffi::OsString;
use std::path::{Path, PathBuf};

#[derive(Clone)]
pub struct Output {
    dir: PathBuf,
    name_begin: OsString,
    name_tail: OsString,
    ext: OsString,
    lim: u32,
}

impl Output {
    pub fn build_path(&self, name_middle: impl Into<OsString>) -> PathBuf {
        let mut name = OsString::new();
        name.push(&self.name_begin);
        name.push(name_middle.into());
        name.push(&self.name_tail);

        let mut path = self.dir.clone();
        path.push(name);
        path.set_extension(&self.ext);

        path
    }

    pub fn get_dir(&self) -> &PathBuf {
        &self.dir
    }

    pub fn lim(mut self, lim: u32) -> Self {
        self.lim = lim;
        self
    }

    pub fn get_lim(&self) -> u32 {
        self.lim
    }

    pub fn default_lim() -> u32 {
        u32::MAX
    }

    pub fn default_input_dir_subdir() -> String {
        "muxed".to_string()
    }

    pub fn from_path(path: impl AsRef<Path>) -> Result<Self, String> {
        let path = path.as_ref();

        let dir = Self::extract_dir(path)?;
        let file_name = match path.file_name() {
            Some(name) => name,
            None => return Ok(Self::empty_with_dir(dir)),
        };

        let (name_begin, name_tail) = Self::split_stem(file_name);
        let ext = Self::extract_extension(file_name);

        Ok(Self {
            dir,
            name_begin,
            name_tail,
            ext,
            lim: Self::default_lim(),
        })
    }
}

pub(in crate::types) enum OutputArg {
    Out,
    Lim,
}

impl ClapArgID for Output {
    type Arg = OutputArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            OutputArg::Out => "output",
            OutputArg::Lim => "output_lim",
        }
    }
}
