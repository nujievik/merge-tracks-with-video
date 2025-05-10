use super::Input;
use crate::i18n::Msg;
use crate::types::{AppError, extensions};
use globset::GlobSet;
use rayon::ThreadPoolBuilder;
use rayon::prelude::*;
use std::ffi::OsStr;
use std::path::{Path, PathBuf};

const LIM_THREADS: usize = 8;

impl Input {
    pub fn try_topmost(mut self) -> Result<Self, AppError> {
        if self.up == 0 {
            return Ok(self);
        }

        let files: Vec<PathBuf> = iter_track_files(&self.dir, self.skip.as_ref())
            .take(self.check as usize)
            .collect();

        let stems: Vec<&OsStr> = files.iter().filter_map(|path| path.file_stem()).collect();

        if stems.is_empty() {
            let msg = format!("{}: {}", Msg::NoInputFiles.get(), self.dir.display());
            return Err(AppError::from(msg));
        }

        let parent_dirs: Vec<PathBuf> = (1..=self.up)
            .scan(self.dir.clone(), |state, _| {
                let parent = state.parent()?.to_path_buf();
                *state = parent.clone();
                Some(parent)
            })
            .collect();

        let pool_result = ThreadPoolBuilder::new().num_threads(LIM_THREADS).build();

        self.topmost = match pool_result {
            Ok(pool) => pool.install(|| parallel_check(parent_dirs, &self, &stems)),
            Err(err) => {
                eprintln!("Warning: {}: {}", Msg::FailCreateThdPool.get(), err);
                parent_dirs
                    .into_par_iter()
                    .find_any(|dir| check_dir(dir, &self, &stems))
            }
        };

        Ok(self)
    }
}

fn is_track_file(path: &Path, skip: Option<&GlobSet>) -> bool {
    if path.is_dir() {
        return false;
    }

    let ext = match path.extension() {
        Some(e) => e,
        None => return false,
    };

    if !extensions::TRACK_IN.contains(ext) {
        return false;
    }

    if let Some(globs) = skip {
        if globs.is_match(path) {
            return false;
        }
    }

    true
}

fn iter_track_files(dir: &Path, skip: Option<&GlobSet>) -> impl Iterator<Item = PathBuf> {
    std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .flat_map(|rd| rd)
        .map(|e| e.path())
        .filter(move |path| is_track_file(path, skip))
}

fn parallel_check(
    parent_dirs: Vec<PathBuf>,
    input: &Input,
    i_stems: &Vec<&OsStr>,
) -> Option<PathBuf> {
    parent_dirs
        .into_par_iter()
        .find_any(|dir| check_dir(dir, input, i_stems))
}

fn os_str_starts_with(prefix: &OsStr, longer: &OsStr) -> bool {
    #[cfg(unix)]
    {
        use std::os::unix::ffi::OsStrExt;
        longer.as_bytes().starts_with(prefix.as_bytes())
    }

    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStrExt;
        longer
            .encode_wide()
            .zip(prefix.encode_wide())
            .all(|(a, b)| a == b)
    }
}

fn check_dir(dir: &Path, input: &Input, i_stems: &[&OsStr]) -> bool {
    let mut count = 0;
    for path in iter_track_files(dir, input.skip.as_ref()) {
        if count >= input.check {
            break;
        }
        count += 1;

        if let Some(stem) = path.file_stem() {
            if i_stems
                .iter()
                .any(|i_stem| os_str_starts_with(stem, i_stem))
            {
                return true;
            }
        }
    }
    false
}
