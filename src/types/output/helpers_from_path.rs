use super::Output;
use std::ffi::{OsStr, OsString};
use std::path::{Path, PathBuf};

impl Output {
    pub(super) fn extract_dir(path: &Path) -> Result<PathBuf, String> {
        let dir = if path.as_os_str().is_empty() {
            let mut muxed_path =
                std::env::current_dir().map_err(|e| format!("Failed to get current dir: {}", e))?;
            muxed_path.push(Self::default_input_dir_subdir());
            muxed_path
        } else if path.is_dir() {
            path.to_path_buf()
        } else if path.to_string_lossy().ends_with(std::path::MAIN_SEPARATOR) {
            path.to_path_buf()
        } else {
            let parent = path
                .parent()
                .filter(|p| !p.as_os_str().is_empty())
                .map(|p| p.to_path_buf());

            match parent {
                Some(p) => p,
                None => {
                    let mut muxed_path = std::env::current_dir()
                        .map_err(|e| format!("Failed to get current dir: {}", e))?;
                    muxed_path.push(Self::default_input_dir_subdir());
                    muxed_path
                }
            }
        };

        let dir = Self::absolutize(dir)?;
        let dir = Self::normalize_no_trailing_separator(dir);

        match Self::is_writable(&dir) {
            true => Ok(dir),
            false => Err(format!("Directory '{}' is not writable", dir.display())),
        }
    }

    fn normalize_no_trailing_separator<P: AsRef<Path>>(path: P) -> PathBuf {
        let path = path.as_ref();
        let mut normalized = PathBuf::new();
        for component in path.components() {
            normalized.push(component);
        }
        normalized
    }

    fn is_writable(target: &Path) -> bool {
        let mut created_dirs = Vec::new();
        let mut path = PathBuf::from(target);

        if path.extension().is_some() {
            path = path.parent().unwrap_or_else(|| Path::new("")).to_path_buf();
        }

        let mut current = path.clone();
        while !current.exists() {
            created_dirs.push(current.clone());
            if let Some(parent) = current.parent() {
                current = parent.to_path_buf();
            } else {
                break;
            }
        }

        fn remove_created_dirs(mut created_dirs: Vec<PathBuf>) {
            created_dirs.reverse();
            for dir in created_dirs {
                let _ = std::fs::remove_dir(dir);
            }
        }

        created_dirs.reverse();
        for dir in &created_dirs {
            if let Err(_) = std::fs::create_dir(dir) {
                remove_created_dirs(created_dirs);
                return false;
            }
        }

        let test_file = path.join(".write_test");
        let result = match std::fs::File::create(&test_file) {
            Ok(_) => {
                let _ = std::fs::remove_file(&test_file);
                true
            }
            Err(_) => false,
        };

        remove_created_dirs(created_dirs);
        result
    }

    fn absolutize<P: AsRef<Path>>(path: P) -> Result<PathBuf, String> {
        let p = path.as_ref();

        let expanded_path = if let Some(home) = home::home_dir() {
            if let Ok(stripped) = p.strip_prefix("~") {
                home.join(stripped)
            } else {
                p.to_path_buf()
            }
        } else {
            p.to_path_buf()
        };

        if expanded_path.is_absolute() {
            Ok(expanded_path)
        } else {
            std::env::current_dir()
                .map(|current_dir| current_dir.join(expanded_path))
                .map_err(|e| e.to_string())
        }
    }

    fn default_ext() -> OsString {
        OsString::from("mkv")
    }

    pub(super) fn empty_with_dir(dir: PathBuf) -> Self {
        Self {
            dir,
            name_begin: OsString::new(),
            name_tail: OsString::new(),
            ext: Self::default_ext(),
            lim: Self::default_lim(),
        }
    }

    pub(super) fn extract_extension(file_name: &OsStr) -> OsString {
        Path::new(file_name)
            .extension()
            .map(OsString::from)
            .unwrap_or_else(|| Self::default_ext())
    }

    pub(super) fn split_stem(file_name: &OsStr) -> (OsString, OsString) {
        let stem = Path::new(file_name).file_stem().unwrap_or(OsStr::new(""));
        let stem_str = stem.to_string_lossy();

        match stem_str.find(',') {
            Some(pos) => {
                let (begin, tail) = stem_str.split_at(pos);
                let tail = &tail[1..];
                (OsString::from(begin), OsString::from(tail))
            }
            None => match stem_str.is_empty() {
                true => (OsString::new(), OsString::new()),
                false => (OsString::from(stem), OsString::new()),
            },
        }
    }
}
