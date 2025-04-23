use std::path::PathBuf;

const TEST_DATA: &str = "tests/test_data";

pub fn data_dir() -> PathBuf {
    let mut dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    dir.push(TEST_DATA);
    dir
}

pub fn data_file(file: &str) -> PathBuf {
    let mut path = data_dir();
    path.push(file);
    path
}
