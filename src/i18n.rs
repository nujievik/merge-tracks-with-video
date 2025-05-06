mod eng;
mod rus;

use crate::types::LangCode;
use std::cell::RefCell;

thread_local! {
    static LANG_CODE: RefCell<LangCode> = RefCell::new(LangCode::default());
}

pub enum Msg<'a> {
    FailGetStartDir,
    FailGetOut,
    FailInitPatterns { s: &'a str },
    FailCheckPkg { s: &'a str, s1: &'a str },
    FailWriteJson { s: &'a str },
    ExeCommand,
    FieldNotHasLim { s: &'a str },
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
            let dflt = LangCode::default();
            eprintln!(
                "Warning: Language '{}' not supported. Use default '{}'",
                lng.as_ref(),
                dflt.as_ref()
            );
            LANG_CODE.with(|code| *code.borrow_mut() = dflt);
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
