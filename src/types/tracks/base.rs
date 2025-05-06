use super::{BaseTracksFields, id::TrackID};
use crate::types::AppError;
use std::collections::HashSet;
use std::str::FromStr;

impl BaseTracksFields {
    pub fn new() -> Self {
        Self {
            no_flag: Self::default_no_flag(),
            inverse: false,
            ids_hashed: None,
            ids_unhashed: None,
        }
    }

    pub fn default_no_flag() -> bool {
        false
    }

    pub fn no_flag(mut self, no_flag: bool) -> Self {
        self.no_flag = no_flag;
        self
    }

    pub fn inverse(mut self, inverse: bool) -> Self {
        self.inverse = inverse;
        self
    }

    fn ids_hashed(mut self, ids: Option<HashSet<TrackID>>) -> Self {
        self.ids_hashed = ids;
        self
    }

    fn ids_unhashed(mut self, ids: Option<Vec<TrackID>>) -> Self {
        self.ids_unhashed = ids;
        self
    }
}

impl FromStr for BaseTracksFields {
    type Err = AppError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();

        let (inverse, s) = if s.starts_with('!') {
            (true, &s[1..])
        } else {
            (false, s)
        };

        let mut ids_hashed: Option<HashSet<TrackID>> = None;
        let mut ids_unhashed: Option<Vec<TrackID>> = None;

        for part in s.split(',').map(str::trim).filter(|s| !s.is_empty()) {
            let id = TrackID::from_str(part)?;
            if id.is_hashable() {
                ids_hashed.get_or_insert_with(HashSet::new).insert(id);
            } else {
                ids_unhashed.get_or_insert_with(Vec::new).push(id);
            }
        }

        if ids_hashed.is_none() && ids_unhashed.is_none() {
            return Err(AppError::from("No track IDs found"));
        }

        Ok(Self::new()
            .inverse(inverse)
            .ids_hashed(ids_hashed)
            .ids_unhashed(ids_unhashed))
    }
}
