mod base;
pub(in crate::types) mod flags;
pub(in crate::types) mod from_arg_matches;
mod id;
pub(in crate::types) mod langs;
pub(in crate::types) mod names;
mod off_on_pro;

use crate::types::LangCode;
use id::TrackID;
use std::collections::{HashMap, HashSet};

#[derive(Clone)]
pub struct Tracks {
    pub audio: BaseTracksFields,
    pub subs: BaseTracksFields,
    pub video: BaseTracksFields,
    pub buttons: BaseTracksFields,
    pub flags: TracksFlags,
    pub names: TracksNames,
    pub langs: TracksLangs,
}

#[derive(Clone)]
pub struct BaseTracksFields {
    pub no_flag: bool,
    pub inverse: bool,
    pub ids_hashed: Option<HashSet<TrackID>>,
    pub ids_unhashed: Option<Vec<TrackID>>,
}

#[derive(Clone)]
pub struct TracksFlags {
    pub defaults: BaseTracksFlagsFields,
    pub forceds: BaseTracksFlagsFields,
    pub enableds: BaseTracksFlagsFields,
}

#[derive(Clone)]
pub struct BaseTracksFlagsFields {
    pub add: Option<bool>,
    pub lim_true: u32,
    pub unmapped: Option<bool>,
    pub map_hashed: Option<HashMap<TrackID, bool>>,
    pub map_unhashed: Option<Vec<(TrackID, bool)>>,
}

#[derive(Clone)]
pub struct TracksNames {
    pub add: Option<bool>,
    pub unmapped: Option<String>,
    pub map_hashed: Option<HashMap<TrackID, String>>,
    pub map_unhashed: Option<Vec<(TrackID, String)>>,
}

#[derive(Clone)]
pub struct TracksLangs {
    pub add: Option<bool>,
    pub unmapped: Option<LangCode>,
    pub map_hashed: Option<HashMap<TrackID, LangCode>>,
    pub map_unhashed: Option<Vec<(TrackID, LangCode)>>,
}
