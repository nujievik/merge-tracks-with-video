/*
mod common;

use mux_media::types::{Tool, ToolPkg, Tools};
use serde_json::from_reader;
use std::ffi::OsStr;
use std::fs::{self, File};
use std::io::BufReader;
use std::path::PathBuf;

fn params_with_json(json: &str) -> ToolExeParams {
    let json = common::data_file(json);
    let mut p = ToolExeParams::new();
    p.json = Some(json);
    p
}

#[test]
fn default_params_are_set() {
    let p = ToolExeParams::new();
    assert_eq!(p.message, "");
    assert!(p.json.is_none());
    assert!(!p.verbose);
}

#[test]
fn are_paths_set() {
    let tools = Tools::new();
    tools.check_package(ToolPackage::Ffmpeg);
    tools.check_package(ToolPackage::Mkvtoolnix);
}

#[test]
fn write_json() {
    let json = common::data_file("output/write_json.json");
    if json.exists() {
        fs::remove_file(&json);
    }

    let tools = Tools::new();
    let params = params_with_json("output/write_json.json");
    let srt = common::data_file("srt.srt");
    let args = [OsStr::new("-i"), OsStr::new(&srt)];
    let _ = tools.execute(Tool::Mkvmerge, &args, Some(&params));

    let file = File::open(&json).expect("Failed to open JSON file");
    let reader = BufReader::new(file);
    let json_args: Vec<String> = from_reader(reader).expect("Failed to parse JSON as Vec<String>");

    let expected_args: Vec<String> = args
        .iter()
        .map(|s| s.to_str().expect("Unsupported UTF-8").to_string())
        .collect();

    assert_eq!(json_args, expected_args);
}

#[cfg(unix)]
#[test]
fn not_panic_on_bad_utf8() {
    use std::os::unix::ffi::OsStrExt;

    let tools = Tools::new();
    let params = params_with_json("output/bad_utf8_unix.json");
    let bad_bytes = &[0x66, 0x6f, 0x6f, 0xFF];
    let args = [OsStr::from_bytes(bad_bytes)];
    assert!(tools.execute(Tool::Mkvmerge, &args, Some(&params)).is_err());
}

#[cfg(windows)]
#[test]
fn not_panic_on_bad_utf8() {
    use std::ffi::OsString;
    use std::os::windows::ffi::OsStringExt;

    let tools = Tools::new();
    let params = params_with_json("output/bad_utf8_win.json");
    let bad_bytes = [0x0066, 0x006F, 0x006F, 0xD800];
    let args = [OsString::from_wide(&bad_bytes)];
    assert!(tools.execute(Tool::Mkvmerge, &args, Some(&params)).is_err());
}

#[test]
fn ok_tool_helps() {
    use strum::IntoEnumIterator;

    let tools = Tools::new();
    let args = ["-h"];
    for tool in Tool::iter() {
        assert!(tools.execute(tool, &args, None).is_ok());
    }
}

#[test]
fn err_incorrect_cmd() {
    let tools = Tools::new();
    assert!(tools.execute(Tool::Mkvmerge, &["incorrect"], None).is_err());
}

#[test]
fn ok_diff_types_args() {
    let tools = Tools::new();
    let mkvmerge = Tool::Mkvmerge;

    assert!(tools.execute(mkvmerge, ["-V"], None).is_ok());
    assert!(tools.execute(mkvmerge, &["-V"], None).is_ok());
    assert!(tools.execute(mkvmerge, vec!["-V"], None).is_ok());
    assert!(tools.execute(mkvmerge, [String::from("-V")], None).is_ok());
    assert!(tools.execute(mkvmerge, [OsStr::new("-V")], None).is_ok());
}

#[test]
fn ok_mkvmerge_i() {
    let tools = Tools::new();
    let path = common::data_file("srt.srt");
    let args = [OsStr::new("-i"), OsStr::new(&path)];
    assert!(tools.execute(Tool::Mkvmerge, &args, None).is_ok());
}

#[test]
fn err_missing_file() {
    let tools = Tools::new();
    let path = common::data_file("missing_file.srt");
    let args = [OsStr::new("-i"), OsStr::new(&path)];
    assert!(tools.execute(Tool::Mkvmerge, &args, None).is_err());
}

/*
#[test]
fn tests_output_dir() {
    let mut dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    dir.push("tests/output");

    println!("{}", dir.display());


    let this_file = Path::new(file!());
    let dir = this_file.parent().unwrap();

}

fn write_to_stdout() {
    println!("Hello, stdout!");
}

#[test]
fn test_stdout_capture() {
    let mut writer = gag::BufferRedirect::stdout().unwrap();

    write_to_stdout();

    let mut buf = String::new();
    writer.read_to_string(&mut buf).unwrap();

    drop(writer);

    println!("CAPTURED OUTPUT: {} \nEND", buf);
    assert!(buf.contains("Hello, stdout!"));
}

#[test]
fn stdout_empty_on_init() {
    let mut writer = gag::BufferRedirect::stdout().unwrap();
    let _params = ToolExeParams::new();
    let _tools = Tools::new();
    let mut buf = String::new();
    writer.read_to_string(&mut buf).unwrap();
    drop(writer);

    println!("CAPTURED OUTPUT: {} \nEND", buf);

    assert!(buf.is_empty());
}
*/
*/
