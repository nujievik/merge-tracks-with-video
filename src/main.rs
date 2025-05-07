use mux_media::traits::TryInit;
use mux_media::types::{AppError, AppConfig, RawAppConfig};

macro_rules! unwrap_or_return {
    ($expr:expr) => {
        match $expr {
            Ok(val) => val,
            Err(AppError { code: 0, message }) => {
                if let Some(msg) = message {
                    println!("{}", msg);
                }
                return Ok(());
            }
            Err(AppError { code, message }) => {
                if let Some(msg) = message {
                    eprintln!("Error: {}", msg);
                }
                return Err(code);
            }
        }
    };
}

fn main() -> Result<(), i32> {
    let cfg = unwrap_or_return!(RawAppConfig::try_init());
    let _cfg = unwrap_or_return!(AppConfig::try_from(cfg));

    Ok(())
}
