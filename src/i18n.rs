use crate::Verbosity;
use fluent::{FluentArgs, FluentBundle, FluentResource};
//use log::{debug, error, info, trace, warn};
use std::rc::Rc;
use unic_langid::LanguageIdentifier;

use once_cell::unsync::Lazy;

thread_local! {
    static BUNDLE: Lazy<FluentBundle<Rc<FluentResource>>> = Lazy::new(|| {
        let lang = Language::from_code("rus");
        let bundle = lang.bundle();
        bundle
    });
}

pub fn get_msg(key: &str, args: Option<&[(&str, &str)]>) -> String {
    BUNDLE.with(|bundle| {
        let msg = match bundle.get_message(key) {
            Some(msg) => msg,
            None => return format!("MISSING MESSAGE, '{}'", key),
        };
        let pattern = match msg.value() {
            Some(value) => value,
            None => return format!("NO VALUE IN MESSAGE, '{}'", key),
        };

        let mut fluent_args = FluentArgs::new();
        if let Some(pairs) = args {
            for (k, v) in pairs {
                fluent_args.set(*k, *v);
            }
        }

        let mut errors = vec![];
        bundle
            .format_pattern(pattern, Some(&fluent_args), &mut errors)
            .to_string()
    })
}

pub fn init_env_logger(verbosity: &Verbosity) {
    env_logger::Builder::new()
        .filter_level(verbosity.to_level_filter())
        .init();
}

/*
 info!("Info message (Normal+)");
 warn!("Something might be wrong");
 error!("Something went wrong");
 debug!("Debug details here");
 trace!("Trace everything");
*/

enum Language {
    Eng,
    Rus,
}

impl Language {
    pub fn from_code(code: &str) -> Self {
        match code {
            "rus" => Language::Rus,
            _ => Language::Eng,
        }
    }

    fn bundle(&self) -> FluentBundle<Rc<FluentResource>> {
        let lang: LanguageIdentifier = match self {
            Language::Eng => "eng".parse().unwrap(),
            Language::Rus => "rus".parse().ok().unwrap_or("eng".parse().unwrap()),
        };

        let ftl_string = match self {
            Language::Eng => include_str!("../locales/eng/main.ftl"),
            Language::Rus => include_str!("../locales/rus/main.ftl"),
        };

        let res = FluentResource::try_new(ftl_string.to_owned()).expect("Failed to parse FTL");

        let mut bundle = FluentBundle::new(vec![lang]);
        bundle
            .add_resource(Rc::new(res))
            .expect("Failed to add FTL to bundle");

        bundle
    }
}
