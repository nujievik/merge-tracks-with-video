pub(in crate::types) mod from_arg_matches;

use super::{BaseTracksFlagsFields, TracksFlags, id::TrackID};
use crate::types::AppError;
use std::collections::HashMap;
use std::str::FromStr;

impl TracksFlags {
    fn default_lim_true_defaults() -> u32 {
        1
    }

    fn default_lim_true_forceds() -> u32 {
        0
    }

    fn default_lim_true_enableds() -> u32 {
        u32::MAX
    }
}

impl BaseTracksFlagsFields {
    pub fn new() -> Self {
        Self {
            add: None,
            lim_true: 0,
            unmapped: None,
            map_hashed: None,
            map_unhashed: None,
        }
    }

    pub fn add(mut self, add: Option<bool>) -> Self {
        self.add = add;
        self
    }

    fn lim_true(mut self, lim: u32) -> Self {
        self.lim_true = lim;
        self
    }

    fn unmapped(mut self, b: Option<bool>) -> Self {
        self.unmapped = b;
        self
    }

    fn map_hashed(mut self, map: Option<HashMap<TrackID, bool>>) -> Self {
        self.map_hashed = map;
        self
    }

    fn map_unhashed(mut self, map: Option<Vec<(TrackID, bool)>>) -> Self {
        self.map_unhashed = map;
        self
    }

    fn parse_bool(s: &str) -> Result<bool, AppError> {
        match s.trim().to_ascii_lowercase().as_str() {
            "1" | "true" | "on" => Ok(true),
            "0" | "false" | "off" => Ok(false),
            _ => Err(AppError::from(format!("Invalid bool key '{}'", s))),
        }
    }
}

impl FromStr for BaseTracksFlagsFields {
    type Err = AppError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if let Ok(b) = Self::parse_bool(s) {
            return Ok(Self::new().unmapped(Some(b)));
        }

        let mut map_hashed: Option<HashMap<TrackID, bool>> = None;
        let mut map_unhashed: Option<Vec<(TrackID, bool)>> = None;

        for part in s.split(',').map(str::trim).filter(|s| !s.is_empty()) {
            let (id, b) = part.rsplit_once(':').unwrap_or((part, "true"));
            let id = TrackID::from_str(id)?;
            let b = Self::parse_bool(b)?;

            if id.is_hashable() {
                map_hashed.get_or_insert_with(HashMap::new).insert(id, b);
            } else {
                map_unhashed.get_or_insert_with(Vec::new).push((id, b));
            }
        }

        if map_hashed.is_none() && map_unhashed.is_none() {
            return Err(AppError::from("No track IDs found"));
        }

        Ok(Self::new()
            .map_hashed(map_hashed)
            .map_unhashed(map_unhashed))
    }
}
