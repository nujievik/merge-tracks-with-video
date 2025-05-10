use mux_media::i18n::Msg;
use mux_media::traits::TryInit;
use mux_media::types::{AppConfig, AppError, RawAppConfig, Tools};

macro_rules! unwrap_or_return {
    ($expr:expr) => {
        match $expr {
            Ok(val) => val,
            Err(err) => {
                let err: AppError = err.into();
                err.print();
                if err.use_stderr() {
                    return Err(err.code);
                } else {
                    return Ok(());
                }
            }
        }
    };
}

fn main() -> Result<(), i32> {
    let cfg = unwrap_or_return!(RawAppConfig::try_init());
    let cfg = unwrap_or_return!(AppConfig::try_from(cfg));
    let _tools = unwrap_or_return!(Tools::try_init());

    cfg.verbosity.set_env_logger();
    Msg::set_lang_code(cfg.locale);

    Ok(())
}
