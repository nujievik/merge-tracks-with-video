use super::{AppConfig, clap_arg_id::AppConfigArg};
use crate::types::output::OutputArg;
use crate::types::traits::{ClapArgID, OffOnPro};
use crate::types::{
    Attachs, Chapters, Input, LangCode, Output, Retiming, Specials, Tracks, Verbosity,
};
use clap::error::ErrorKind;
use clap::{ArgMatches, Error, FromArgMatches};

impl FromArgMatches for AppConfig {
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

        let lim = match matches
            .try_remove_one::<u32>(Output::as_str(OutputArg::Lim))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(u) => u,
            None => Output::default_lim(),
        };

        let output = match matches
            .try_remove_one::<Output>(Output::as_str(OutputArg::Out))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(out) => out.lim(lim),
            None => {
                let mut path = input.get_dir();
                path.push(Output::default_input_dir_subdir());
                Output::from_path(path)
                    .map_err(|e| Error::raw(ErrorKind::ValueValidation, e.to_string()))?
            }
        };

        let verbosity = Verbosity::from_arg_matches_mut(matches)?;

        let locale = match matches
            .try_remove_one::<LangCode>(AppConfig::as_str(AppConfigArg::Locale))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(lng) => lng,
            None => LangCode::default(),
        };

        let exit_on_err = match matches
            .try_remove_one::<bool>(AppConfig::as_str(AppConfigArg::ExitOnErr))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(b) => b,
            None => false,
        };

        let pro = match matches
            .try_remove_one::<bool>(AppConfig::as_str(AppConfigArg::Pro))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(b) => b,
            None => false,
        };

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
