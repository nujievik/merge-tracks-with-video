use super::{AppConfig, raw::RawAppConfig};
use crate::types::AppError;
use clap::{CommandFactory, FromArgMatches};

impl TryFrom<RawAppConfig> for AppConfig {
    type Error = AppError;

    fn try_from(value: RawAppConfig) -> Result<Self, Self::Error> {
        let mut matches = Self::command().try_get_matches_from(value.args)?;
        let cfg = Self::from_arg_matches_mut(&mut matches)?;
        Ok(cfg)
    }
}
