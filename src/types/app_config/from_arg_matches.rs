use super::{AppConfig, clap_arg_id::AppConfigArg};
use crate::traits::{ClapArgID, OffOnPro};
use crate::types::{
    AppError, Attachs, Chapters, Input, LangCode, Output, Retiming, Specials, Tracks, Verbosity,
};
use crate::val_from_matches;
use clap::{ArgMatches, Error};

impl clap::FromArgMatches for AppConfig {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let input = Input::from_arg_matches_mut(matches)?;

        let lim = val_from_matches!(matches, u32, AppConfigArg::Lim, Output::default_lim);
        let output = val_from_matches!(
            matches,
            Output,
            AppConfigArg::Output,
            || Output::try_from(&input),
            try_default
        )
        .lim(lim);

        let verbosity = Verbosity::from_arg_matches_mut(matches)?;
        let locale = val_from_matches!(matches, LangCode, AppConfigArg::Locale, LangCode::default);
        let exit_on_err = val_from_matches!(
            matches,
            bool,
            AppConfigArg::ExitOnErr,
            Self::default_exit_on_err
        );
        let pro = val_from_matches!(matches, bool, AppConfigArg::Pro, Self::default_pro);

        let retiming = Retiming::from_arg_matches_mut(matches)?;
        let tracks = Tracks::from_arg_matches_mut(matches)?.off_on_pro(pro);
        let chapters = Chapters::from_arg_matches_mut(matches)?;
        let attachs = Attachs::from_arg_matches_mut(matches)?.off_on_pro(pro);
        let specials = Specials::from_arg_matches_mut(matches)?;

        Ok(Self {
            input,
            output,
            verbosity,
            locale,
            exit_on_err,
            retiming,
            tracks,
            chapters,
            attachs,
            specials,
        })
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}
