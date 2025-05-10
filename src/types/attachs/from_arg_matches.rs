use super::{Attachs, BaseAttachsFields};
use crate::{traits::ClapArgID, types::AppError, val_from_matches};
use clap::{ArgMatches, Error, FromArgMatches};

#[derive(Clone, Copy)]
pub enum AttachsArg {
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
        let fonts = Self::base_from_matches(matches, AttachsArg::Fonts, AttachsArg::NoFonts)?;
        let other = Self::base_from_matches(matches, AttachsArg::Attachs, AttachsArg::NoAttachs)?;

        let sort_fonts = val_from_matches!(matches, bool, AttachsArg::SortFonts, AttachsArg::NoSortFonts, @off_on_pro);

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

impl Attachs {
    fn base_from_matches(
        matches: &mut ArgMatches,
        arg: AttachsArg,
        no_arg: AttachsArg,
    ) -> Result<BaseAttachsFields, Error> {
        Ok(
            if val_from_matches!(matches, bool, no_arg, BaseAttachsFields::default_no_flag) {
                BaseAttachsFields::new().no_flag(true)
            } else {
                val_from_matches!(matches, BaseAttachsFields, arg, BaseAttachsFields::new)
            },
        )
    }
}
