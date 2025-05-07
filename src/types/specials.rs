pub(in crate::types) mod from_arg_matches;
mod special_opt;

use crate::types::AppError;
use special_opt::SpecialOpt;
use std::str::FromStr;

#[derive(Clone)]
pub struct Specials {
    pub all: Option<Vec<String>>,
}

impl Specials {
    fn new() -> Self {
        Self { all: None }
    }
}

impl FromStr for Specials {
    type Err = AppError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let mut specials = Vec::new();

        for part in s.split_whitespace() {
            if part.starts_with('-') {
                SpecialOpt::from_str(part.trim_start_matches('-'))
                    .map_err(|_| AppError::from(format!("unexpected argument: '{}'", part)))?;
                specials.push(part.to_string());
            } else {
                specials.push(part.to_string());
            }
        }

        if specials.is_empty() {
            return Err(AppError::from("No special options found"));
        }

        Ok(Specials {
            all: Some(specials),
        })
    }
}
