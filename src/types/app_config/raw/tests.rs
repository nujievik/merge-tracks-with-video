use super::*;

fn oss(args: &[&str]) -> Vec<OsString> {
    args.iter().map(|s| OsString::from(s)).collect()
}

fn run_with_args(args: &[&str]) -> RawAppConfig {
    RawAppConfig::new_from_args(oss(args)).expect("Should parse args without error")
}

#[test]
fn test_basic_split() {
    let raw = run_with_args(&[
        "arg1",
        "arg2",
        "--target",
        "video",
        "--opt1",
        "--opt2",
        "--target",
        "audio",
        "--opt3",
        "--target",
        "global",
        "--g1",
        "--g2",
        "--mkvmerge",
        "-o",
        "out.mkv",
    ]);

    assert_eq!(raw.args, oss(&["arg1", "arg2", "--g1", "--g2"]));

    let map = raw.trg_args.unwrap();
    assert_eq!(
        map.get(&Target::Group(TargetGroup::Video)).unwrap(),
        &oss(&["--opt1", "--opt2"])
    );
    assert_eq!(
        map.get(&Target::Group(TargetGroup::Audio)).unwrap(),
        &oss(&["--opt3"])
    );

    match &raw.call_tool {
        Some((Tool::Mkvmerge, args)) => {
            assert_eq!(args, &oss(&["-o", "out.mkv"]));
        }
        _ => panic!("Expected Tool::Mkvmerge"),
    }
}

#[test]
fn test_path_target() {
    let current_dir = std::path::Path::new(file!())
        .parent()
        .expect("Should get parent directory")
        .to_path_buf();

    let dir_str = current_dir.to_str().unwrap();

    let raw = run_with_args(&["--target", dir_str, "--x", "--y", "--mkvinfo"]);

    match raw.call_tool {
        Some((Tool::Mkvinfo, _)) => {}
        _ => panic!("Expected mkvinfo tool"),
    }

    let canonical_dir = current_dir.canonicalize().unwrap();
    let target_key = Target::Path(canonical_dir);

    let map = raw.trg_args.unwrap();
    assert!(map.contains_key(&target_key));
    assert_eq!(map.get(&target_key).unwrap(), &oss(&["--x", "--y"]));
}

#[test]
fn test_subs_alias() {
    let raw = run_with_args(&[
        "--target",
        "subtitles",
        "--opt_sub",
        "--target",
        "subs",
        "--opt_s",
    ]);

    let map = raw.trg_args.unwrap();
    assert_eq!(
        map.get(&Target::Group(TargetGroup::Subs)).unwrap(),
        &oss(&["--opt_sub", "--opt_s"])
    );
}

#[test]
fn test_only_tool() {
    let raw = run_with_args(&["--mkvextract", "file.mkv"]);

    assert!(raw.args.is_empty());
    assert!(raw.trg_args.is_none());
    assert_eq!(raw.call_tool, Some((Tool::Mkvextract, oss(&["file.mkv"]))));
}

#[test]
fn test_list_langs_flags() {
    let raw1 = run_with_args(&["--list-langs"]);
    assert!(raw1.list_langs);
    assert!(!raw1.list_targets);
    assert!(raw1.call_tool.is_none());
    assert!(raw1.args.is_empty());
    assert!(raw1.trg_args.is_none());

    let raw2 = run_with_args(&["--list-languages"]);
    assert!(raw2.list_langs);
    assert!(!raw2.list_targets);
    assert!(raw2.call_tool.is_none());
    assert!(raw2.args.is_empty());
    assert!(raw2.trg_args.is_none());
}

#[test]
fn test_list_targets_flag() {
    let raw = run_with_args(&["--list-targets"]);
    assert!(!raw.list_langs);
    assert!(raw.list_targets);
    assert!(raw.call_tool.is_none());
    assert!(raw.args.is_empty());
    assert!(raw.trg_args.is_none());
}

#[test]
fn test_fail_nonexistent_path() {
    let result = RawAppConfig::new_from_args(oss(&["--target", "nonexistent/path", "--opt"]));
    assert!(result.is_err());

    if let Err(err) = result {
        assert!(
            err.to_string().contains("Incorrect path target"),
            "Unexpected error message: {}",
            err
        );
    }
}

#[test]
fn test_args_before_target() {
    let raw = run_with_args(&["--arg1", "--target", "audio", "--opt"]);
    let map = raw.trg_args.unwrap();

    assert_eq!(raw.args, oss(&["--arg1"]));
    assert_eq!(
        map.get(&Target::Group(TargetGroup::Audio)).unwrap(),
               &oss(&["--opt"])
    );
}

#[test]
fn test_multiple_target_switching() {
    let raw = run_with_args(&[
        "init_arg", "--target", "audio", "--a1", "--target", "video", "--v1", "--target", "global",
        "--g1", "--target", "audio", "--a2", "--target", "video", "--v2",
    ]);

    let map = raw.trg_args.unwrap();

    assert_eq!(raw.args, oss(&["init_arg", "--g1"]));

    assert_eq!(
        map.get(&Target::Group(TargetGroup::Audio)).unwrap(),
        &oss(&["--a1", "--a2"])
    );
    assert_eq!(
        map.get(&Target::Group(TargetGroup::Video)).unwrap(),
        &oss(&["--v1", "--v2"])
    );
}

#[test]
fn test_empty_input() {
    let raw = run_with_args(&[]);
    assert!(!raw.list_langs);
    assert!(!raw.list_targets);
    assert!(raw.call_tool.is_none());
    assert!(raw.args.is_empty());
    assert!(raw.trg_args.is_none());
}
