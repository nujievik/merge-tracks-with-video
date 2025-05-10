mod eng;
mod rus;

use crate::types::LangCode;
use std::cell::RefCell;

thread_local! {
    static LANG_CODE: RefCell<LangCode> = RefCell::new(LangCode::default());
}

pub enum Msg<'a> {
    ExeCommand,
    FailCreateThdPool,
    FailSetPaths { s: &'a str, s1: &'a str },
    FailWriteJson { s: &'a str },
    NoInputFiles,
    UnsupLngLog { s: &'a str, s1: &'a str },
}

impl<'a> Msg<'a> {
    pub fn get(self) -> String {
        match Self::get_lang_code() {
            LangCode::Eng => eng::eng(self),
            LangCode::Rus => rus::rus(self),
            _ => eng::eng(self),
        }
    }

    pub fn set_lang_code(lng: LangCode) {
        if Self::is_supported_lang(&lng) {
            LANG_CODE.with(|code| *code.borrow_mut() = lng);
        } else {
            LANG_CODE.with(|code| {
                let using = code.borrow();
                eprintln!(
                    "Warning: {}",
                    Msg::UnsupLngLog {
                        s: lng.as_ref(),
                        s1: using.as_ref()
                    }
                    .get()
                );
            });
        }
    }

    fn is_supported_lang(lng: &LangCode) -> bool {
        match lng {
            LangCode::Eng => true,
            LangCode::Rus => true,
            _ => false,
        }
    }

    fn get_lang_code() -> LangCode {
        LANG_CODE.with(|code| code.borrow().clone())
    }
}
