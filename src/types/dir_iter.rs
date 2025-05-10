use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;
use walkdir::{DirEntry, IntoIter, WalkDir};

pub struct DirIter {
    seen: HashSet<PathBuf>,
    walker: IntoIter,
}

impl DirIter {
    pub fn new<P: Into<PathBuf>>(root: P) -> Self {
        let walker = WalkDir::new(root.into()).follow_links(false).into_iter();

        Self {
            seen: HashSet::new(),
            walker,
        }
    }

    fn is_symlink_dir(entry: &DirEntry) -> bool {
        entry.file_type().is_symlink()
            && entry.path_is_symlink()
            && fs::metadata(entry.path())
                .map(|meta| meta.is_dir())
                .unwrap_or(false)
    }
}

impl Iterator for DirIter {
    type Item = PathBuf;

    fn next(&mut self) -> Option<Self::Item> {
        while let Some(entry_result) = self.walker.next() {
            match entry_result {
                Ok(entry) => {
                    if entry.file_type().is_dir() && !entry.path_is_symlink() {
                        if let Ok(real_path) = fs::canonicalize(entry.path()) {
                            if self.seen.insert(real_path.clone()) {
                                return Some(real_path);
                            }
                        }
                    } else if Self::is_symlink_dir(&entry) {
                        if let Ok(real_path) = fs::canonicalize(entry.path()) {
                            if self.seen.insert(real_path.clone()) {
                                return Some(real_path);
                            }
                        }
                    }
                }
                Err(_) => continue,
            }
        }
        None
    }
}
