use super::common;

use common::{data_dir, data_file};
use mux_media::Output;
use serial_test::serial;
use std::path::PathBuf;

#[test]
fn build_path() {
    let path = data_file("file_,_part.mp4");
    let output = Output::from_path(&path).unwrap();

    let result = output.build_path("01");
    let expected = data_file("file_01_part.mp4");

    assert_eq!(result, expected);
}

#[test]
fn err_not_writable_path() {
    let result = Output::from_path("/");

    if let Err(err) = result {
        let err_msg = format!("{}", err);
        assert!(
            err_msg.contains("is not writable"),
            "Expected error message to contain 'is not writable', but got: {}",
            err_msg
        );
    } else {
        panic!("Expected Err, but got Ok");
    }
}

#[test]
#[serial]
fn build_path_with_empty_dir() {
    let output = Output::from_path("file_,_part.mp4").unwrap();

    let result = output.build_path("01");
    let mut expected = PathBuf::from(std::env::current_dir().unwrap());
    expected.push("merged");
    expected.push("file_01_part.mp4");

    assert_eq!(result, expected);
}

#[test]
fn build_path_with_empty_tail() {
    let path = data_file("file_.mp4");
    let output = Output::from_path(&path).unwrap();

    let result = output.build_path("01");
    let expected = data_file("file_01.mp4");

    assert_eq!(result, expected);
}

#[test]
fn build_path_with_empty_ext() {
    let path = data_file("file_,_part");
    let output = Output::from_path(&path).unwrap();

    let result = output.build_path("01");
    let expected = data_file("file_01_part.mkv");

    assert_eq!(result, expected);
}

#[test]
#[serial]
fn build_path_empty() {
    let output = Output::from_path("").unwrap();

    let result = output.build_path("01");
    let mut expected = PathBuf::from(std::env::current_dir().unwrap());
    expected.push("merged");
    expected.push("01.mkv");

    assert_eq!(result, expected);
}

#[test]
fn dir_access() {
    let path = data_file("file_,_part");
    let output = Output::from_path(&path).unwrap();

    let dir = data_dir();
    assert_eq!(output.dir, dir);
}
