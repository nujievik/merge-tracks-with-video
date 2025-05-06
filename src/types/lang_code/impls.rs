use super::LangCode;
use super::list_langs::LIST_LANGS;
use super::map_from_str::MAP_FROM_STR;
use std::str::FromStr;

impl Default for LangCode {
    fn default() -> Self {
        LangCode::Eng
    }
}

impl FromStr for LangCode {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, <LangCode as FromStr>::Err> {
        MAP_FROM_STR
            .get(s)
            .copied()
            .ok_or_else(|| format!("Invalid language code: '{}'", s))
    }
}

impl LangCode {
    pub fn print_list_langs() {
        println!("{}", LIST_LANGS)
    }
}
