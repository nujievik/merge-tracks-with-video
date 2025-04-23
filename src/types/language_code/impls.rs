use super::{LanguageCode, map};

impl LanguageCode {
    pub fn from_str(code: &str) -> Result<Self, String> {
        map::LANG_MAP
            .get(code)
            .copied()
            .ok_or_else(|| format!("Invalid language code: '{}'", code))
    }
}
