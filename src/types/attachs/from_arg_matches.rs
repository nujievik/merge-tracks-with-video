use super::{Attachs, BaseAttachsFields};
use crate::types::traits::ClapArgID;
use clap::{ArgMatches, Error, FromArgMatches, error::ErrorKind};

#[derive(Clone, Copy)]
pub(in crate::types) enum AttachsArg {
    HelpSortFonts,
    SortFonts,
    NoSortFonts,
    Attachs,
    NoAttachs,
    Fonts,
    NoFonts,
}

impl ClapArgID for Attachs {
    type Arg = AttachsArg;

    fn as_str(arg: Self::Arg) -> &'static str {
        match arg {
            AttachsArg::HelpSortFonts => "help_sort_fonts",
            AttachsArg::SortFonts => "sort_fonts",
            AttachsArg::NoSortFonts => "no_sort_fonts",
            AttachsArg::Attachs => "attachs",
            AttachsArg::NoAttachs => "no_attachs",
            AttachsArg::Fonts => "fonts",
            AttachsArg::NoFonts => "no_fonts",
        }
    }
}

impl FromArgMatches for Attachs {
    fn from_arg_matches(matches: &ArgMatches) -> Result<Self, Error> {
        let mut matches = matches.clone();
        Self::from_arg_matches_mut(&mut matches)
    }

    fn update_from_arg_matches(&mut self, matches: &ArgMatches) -> Result<(), Error> {
        let mut matches = matches.clone();
        self.update_from_arg_matches_mut(&mut matches)
    }

    fn from_arg_matches_mut(matches: &mut ArgMatches) -> Result<Self, Error> {
        let fonts = base_fields_from_matches(matches, AttachsArg::Fonts, AttachsArg::NoFonts)?;
        let other = base_fields_from_matches(matches, AttachsArg::Attachs, AttachsArg::NoAttachs)?;

        let sort_fonts = match matches
            .try_remove_one::<bool>(Attachs::as_str(AttachsArg::SortFonts))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(true) => Some(true),
            _ => {
                match matches
                    .try_remove_one::<bool>(Attachs::as_str(AttachsArg::NoSortFonts))
                    .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
                {
                    Some(true) => Some(false),
                    _ => None,
                }
            }
        };

        Ok(Self {
            fonts,
            other,
            sort_fonts,
        })
    }

    fn update_from_arg_matches_mut(&mut self, matches: &mut ArgMatches) -> Result<(), Error> {
        *self = Self::from_arg_matches_mut(matches)?;
        Ok(())
    }
}

fn base_fields_from_matches(
    matches: &mut ArgMatches,
    arg: AttachsArg,
    no_arg: AttachsArg,
) -> Result<BaseAttachsFields, Error> {
    let no_flag = match matches
        .try_remove_one::<bool>(Attachs::as_str(no_arg))
        .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
    {
        Some(b) => b,
        None => BaseAttachsFields::default_no_flag(),
    };

    let base = if no_flag {
        BaseAttachsFields::new().no_flag(true)
    } else {
        match matches
            .try_remove_one::<BaseAttachsFields>(Attachs::as_str(arg))
            .map_err(|e| Error::raw(ErrorKind::UnknownArgument, e.to_string()))?
        {
            Some(base) => base,
            None => BaseAttachsFields::new(),
        }
    };

    Ok(base)
}
