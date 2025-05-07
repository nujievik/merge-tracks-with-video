pub(in crate::types) mod from_arg_matches;

use super::{TracksLangs, id::TrackID};
use crate::types::{AppError, LangCode};
use std::collections::HashMap;
use std::str::FromStr;

impl TracksLangs {
    pub fn new() -> Self {
        Self {
            add: None,
            unmapped: None,
            map_hashed: None,
            map_unhashed: None,
        }
    }

    pub fn add(mut self, b: Option<bool>) -> Self {
        self.add = b;
        self
    }

    fn unmapped(mut self, name: Option<LangCode>) -> Self {
        self.unmapped = name;
        self
    }

    fn map_hashed(mut self, map: Option<HashMap<TrackID, LangCode>>) -> Self {
        self.map_hashed = map;
        self
    }

    fn map_unhashed(mut self, map: Option<Vec<(TrackID, LangCode)>>) -> Self {
        self.map_unhashed = map;
        self
    }
}

impl FromStr for TracksLangs {
    type Err = AppError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();

        if !s.contains(':') {
            return Ok(Self::new().unmapped(Some(LangCode::from_str(s)?)));
        }

        let mut map_hashed: Option<HashMap<TrackID, LangCode>> = None;
        let mut map_unhashed: Option<Vec<(TrackID, LangCode)>> = None;

        for part in s.split(',').map(str::trim).filter(|s| !s.is_empty()) {
            let (id, lng) = part
                .split_once(':')
                .ok_or(AppError::from("Invalid format: Must be [n:]L[,m:L]..."))?;
            let id = TrackID::from_str(id)?;
            let lng = LangCode::from_str(lng)?;

            if id.is_hashable() {
                map_hashed.get_or_insert_with(HashMap::new).insert(id, lng);
            } else {
                map_unhashed.get_or_insert_with(Vec::new).push((id, lng));
            }
        }

        if map_hashed.is_none() && map_unhashed.is_none() {
            return Err(AppError::from("No languages found"));
        }

        Ok(Self::new()
            .map_hashed(map_hashed)
            .map_unhashed(map_unhashed))
    }
}
