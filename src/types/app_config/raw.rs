use crate::types::Tool;

use std::collections::HashMap;
use std::ffi::OsString;
use std::path::PathBuf;
use strum_macros::{Display, EnumString};

#[derive(Debug, EnumString, Display, Clone, Copy, PartialEq, Eq, Hash)]
#[strum(serialize_all = "kebab-case")]
pub enum TargetGroup {
    Audio,
    Video,
    Signs,
    #[strum(serialize = "subs")]
    #[strum(serialize = "subtitles")]
    Subs,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Target {
    Group(TargetGroup),
    Path(PathBuf),
}

#[derive(Debug)]
pub struct RawAppConfig {
    pub list_langs: bool,
    pub list_targets: bool,
    pub call_tool: Option<(Tool, Vec<OsString>)>,
    pub args: Vec<OsString>,
    pub trg_args: HashMap<Target, Vec<OsString>>,
}

impl RawAppConfig {
    pub fn new() -> Self {
        let args: Vec<OsString> = std::env::args_os().skip(1).collect();
        Self::new_from_args(args)
    }

    fn parse_target(arg: &OsString) -> Target {
        let s = arg.to_string_lossy();
        if let Ok(group) = s.parse::<TargetGroup>() {
            Target::Group(group)
        } else {
            let path = PathBuf::from(arg.clone());
            if path.exists() {
                Target::Path(path.canonicalize().unwrap_or(path))
            } else {
                Target::Path(path)
            }
        }
    }

    fn new_from_args(in_args: Vec<OsString>) -> Self {
        let mut list_langs = false;
        let mut list_targets = false;
        let mut call_tool: Option<(Tool, Vec<OsString>)> = None;
        let mut args: Vec<OsString> = Vec::new();
        let mut trg_args: HashMap<Target, Vec<OsString>> = HashMap::new();
        let mut current_target: Option<Target> = None;

        let mut iter = in_args.into_iter().peekable();

        while let Some(arg) = iter.next() {
            let s = arg.to_string_lossy();

            if s == "--list-langs" || s == "--list-languages" {
                list_langs = true;
                break;
            }

            if s == "--list-targets" {
                list_targets = true;
                break;
            }

            if s.starts_with("--") {
                let maybe_tool = &s[2..];
                if let Ok(tool) = maybe_tool.parse::<Tool>() {
                    let remaining_args: Vec<OsString> = iter.collect();
                    call_tool = Some((tool, remaining_args));
                    break;
                }
            }

            match s.as_ref() {
                "--target" | "-t" => {
                    if let Some(trg_arg) = iter.next() {
                        let trg_str = trg_arg.to_string_lossy();
                        if trg_str == "global" {
                            current_target = None;
                        } else {
                            let target = Self::parse_target(&trg_arg);
                            current_target = Some(target.clone());
                            trg_args.entry(target).or_insert_with(Vec::new);
                        }
                    }
                }
                _ => {
                    if let Some(target) = &current_target {
                        trg_args.get_mut(target).unwrap().push(arg);
                    } else {
                        args.push(arg);
                    }
                }
            }
        }

        Self {
            list_langs,
            list_targets,
            call_tool,
            args,
            trg_args,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::OsString;
    use std::path::PathBuf;

    fn oss(args: &[&str]) -> Vec<OsString> {
        args.iter().map(|s| OsString::from(s)).collect()
    }

    fn run_with_args(args: &[&str]) -> RawAppConfig {
        RawAppConfig::new_from_args(oss(args))
    }

    #[test]
    fn basic_split() {
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

        assert_eq!(
            raw.trg_args
                .get(&Target::Group(TargetGroup::Video))
                .unwrap(),
            &oss(&["--opt1", "--opt2"])
        );

        assert_eq!(
            raw.trg_args
                .get(&Target::Group(TargetGroup::Audio))
                .unwrap(),
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
    fn path_target() {
        let raw = run_with_args(&["--target", "some/folder", "--x", "--y", "--mkvinfo"]);

        match raw.call_tool {
            Some((Tool::Mkvinfo, _)) => {}
            _ => panic!("Expected mkvinfo tool"),
        }

        let target_key = Target::Path(PathBuf::from("some/folder"));

        assert!(raw.trg_args.contains_key(&target_key));
        assert_eq!(
            raw.trg_args.get(&target_key).unwrap(),
            &oss(&["--x", "--y"])
        );
    }

    #[test]
    fn subs_alias() {
        let raw = run_with_args(&[
            "--target",
            "subtitles",
            "--opt_sub",
            "--target",
            "subs",
            "--opt_s",
        ]);

        assert_eq!(
            raw.trg_args.get(&Target::Group(TargetGroup::Subs)).unwrap(),
            &oss(&["--opt_sub", "--opt_s"])
        );
    }

    #[test]
    fn only_tool() {
        let raw = run_with_args(&["--mkvextract", "file.mkv"]);

        assert!(raw.args.is_empty());
        assert!(raw.trg_args.is_empty());
        assert_eq!(raw.call_tool, Some((Tool::Mkvextract, oss(&["file.mkv"]))));
    }

    #[test]
    fn list_langs_flags() {
        let raw1 = run_with_args(&["--list-langs"]);
        assert!(raw1.list_langs);
        assert!(!raw1.list_targets);
        assert!(raw1.call_tool.is_none());
        assert!(raw1.args.is_empty());
        assert!(raw1.trg_args.is_empty());

        let raw2 = run_with_args(&["--list-languages"]);
        assert!(raw2.list_langs);
        assert!(!raw2.list_targets);
        assert!(raw2.call_tool.is_none());
        assert!(raw2.args.is_empty());
        assert!(raw2.trg_args.is_empty());
    }

    #[test]
    fn list_targets_flag() {
        let raw = run_with_args(&["--list-targets"]);
        assert!(!raw.list_langs);
        assert!(raw.list_targets);
        assert!(raw.call_tool.is_none());
        assert!(raw.args.is_empty());
        assert!(raw.trg_args.is_empty());
    }

    #[test]
    fn nonexistent_path_target() {
        let raw = run_with_args(&["--target", "nonexistent/path", "--opt"]);

        let key = Target::Path(PathBuf::from("nonexistent/path"));
        assert!(raw.trg_args.contains_key(&key));
        assert_eq!(raw.trg_args.get(&key).unwrap(), &oss(&["--opt"]));
    }

    #[test]
    fn multiple_target_switching() {
        let raw = run_with_args(&[
            "init_arg", "--target", "audio", "--a1", "--target", "video", "--v1", "--target",
            "global", "--g1", "--target", "audio", "--a2", "--target", "video", "--v2",
        ]);

        assert_eq!(raw.args, oss(&["init_arg", "--g1"]));

        assert_eq!(
            raw.trg_args
                .get(&Target::Group(TargetGroup::Audio))
                .unwrap(),
            &oss(&["--a1", "--a2"])
        );

        assert_eq!(
            raw.trg_args
                .get(&Target::Group(TargetGroup::Video))
                .unwrap(),
            &oss(&["--v1", "--v2"])
        );
    }

    #[test]
    fn args_before_target() {
        let raw = run_with_args(&["--arg1", "--target", "audio", "--opt"]);

        assert_eq!(raw.args, oss(&["--arg1"]));
        assert_eq!(
            raw.trg_args
                .get(&Target::Group(TargetGroup::Audio))
                .unwrap(),
            &oss(&["--opt"])
        );
    }

    #[test]
    fn empty_input() {
        let raw = run_with_args(&[]);
        assert!(!raw.list_langs);
        assert!(!raw.list_targets);
        assert!(raw.call_tool.is_none());
        assert!(raw.args.is_empty());
        assert!(raw.trg_args.is_empty());
    }
}
