use mux_media::init::init;
use mux_media::types::AppFlow;

macro_rules! unwrap_or_return_main {
    ($expr:expr) => {
        match $expr {
            AppFlow::Proceed(val) => val,
            AppFlow::Done => return Ok(()),
            AppFlow::Fail(e) => {
                eprintln!("Error: {}", e);
                return Err(1);
            }
        }
    };
}

fn main() -> Result<(), i8> {
    let (_cfg, _tools) = unwrap_or_return_main!(init());

    Ok(())
}
