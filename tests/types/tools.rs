use super::common;
use mux_media::types::{Tool, Tools};
use serde_json::from_reader;
use std::ffi::OsStr;
use std::fs::{self, File};
use std::io::BufReader;

fn init() -> Tools {
    Tools::new().try_set_paths(Tool::iter()).unwrap()
}

fn init_with_json(name: &str) -> Tools {
    let json = common::data_file(name);
    init().json(&json)
}

#[test]
fn test_set_all_paths() {
    init();
}

#[test]
fn test_write_json() {
    let json = common::data_file("output/write_json.json");
    let _ = fs::remove_file(&json);

    let tools = init().json(&json);

    let srt = common::data_file("srt.srt");
    let args = ["-i".to_string(), srt.to_string_lossy().into_owned()];

    assert!(tools.execute(&Tool::Mkvmerge, &args, None).is_ok());

    let file = File::open(&json).expect("Failed to open JSON file");
    let reader = BufReader::new(file);
    let json_args: Vec<String> = from_reader(reader).expect("Failed to parse JSON as Vec<String>");

    assert_eq!(json_args, args);
}

#[cfg(unix)]
#[test]
fn test_not_panic_on_bad_utf8() {
    use std::os::unix::ffi::OsStrExt;

    let tools = init_with_json("output/bad_utf8_unix.json");
    let bad_bytes = &[0x66, 0x6f, 0x6f, 0xFF];
    let args = [OsStr::from_bytes(bad_bytes)];
    assert!(tools.execute(&Tool::Mkvmerge, &args, None).is_err());
}

#[cfg(windows)]
#[test]
fn test_not_panic_on_bad_utf8() {
    use std::ffi::OsString;
    use std::os::windows::ffi::OsStringExt;

    let tools = init_with_json("output/bad_utf8_win.json");
    let bad_bytes = [0x0066, 0x006F, 0x006F, 0xD800];
    let args = [OsString::from_wide(&bad_bytes)];
    assert!(tools.execute(&Tool::Mkvmerge, &args, None).is_err());
}

#[test]
fn test_tool_helps() {
    let tools = init();
    let args = ["-h"];
    for tool in Tool::iter() {
        assert!(tools.execute(&tool, &args, None).is_ok());
    }
}

#[test]
fn test_err_incorrect_cmd() {
    let tools = init();
    assert!(
        tools
            .execute(&Tool::Mkvmerge, &["incorrect"], None)
            .is_err()
    );
}

#[test]
fn test_mkvmerge_i() {
    let tools = init();
    let path = common::data_file("srt.srt");
    let args = [OsStr::new("-i"), OsStr::new(&path)];
    assert!(tools.execute(&Tool::Mkvmerge, &args, None).is_ok());
}

#[test]
fn test_err_missing_file() {
    let tools = init();
    let path = common::data_file("missing_file.srt");
    let args = [OsStr::new("-i"), OsStr::new(&path)];
    assert!(tools.execute(&Tool::Mkvmerge, &args, None).is_err());
}
