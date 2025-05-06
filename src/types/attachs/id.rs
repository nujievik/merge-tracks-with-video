use crate::types::AppError;
use crate::types::RangeU32;
use std::str::FromStr;

#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum AttachID {
    U32(u32),
    RangeU32(RangeU32),
}

impl AttachID {
    pub fn is_hashable(&self) -> bool {
        matches!(self, AttachID::U32(_))
    }
}

impl FromStr for AttachID {
    type Err = AppError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();

        if let Ok(n) = s.parse::<u32>() {
            Ok(Self::U32(n))
        } else if let Ok(rng) = RangeU32::from_str(s) {
            Ok(Self::RangeU32(rng))
        } else {
            Err(AppError::from(format!(
                "Invalid attach ID '{}' (must be num or range (n-m) of num)",
                s
            )))
        }
    }
}
