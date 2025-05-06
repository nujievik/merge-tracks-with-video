use crate::types::{AppError, LangCode, RangeU32};
use std::str::FromStr;

#[derive(Clone, Eq, Copy, Hash, PartialEq)]
pub enum TrackID {
    U32(u32),
    RangeU32(RangeU32),
    LangCode(LangCode),
}

impl TrackID {
    pub fn is_hashable(&self) -> bool {
        match self {
            TrackID::RangeU32(_) => false,
            _ => true,
        }
    }
}

impl FromStr for TrackID {
    type Err = AppError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();

        if let Ok(n) = s.parse::<u32>() {
            Ok(Self::U32(n))
        } else if let Ok(rng) = RangeU32::from_str(s) {
            Ok(Self::RangeU32(rng))
        } else {
            match LangCode::from_str(s) {
                Ok(code) => Ok(Self::LangCode(code)),
                Err(_) => Err(AppError::from(format!(
                    "Invalid track ID '{}' (must be num, range (n-m) of num or lang code)",
                    s
                ))),
            }
        }
    }
}
