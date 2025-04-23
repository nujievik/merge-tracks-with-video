use crate::Tool;
use std::collections::HashMap;
use std::env;
use std::ffi::OsString;
use std::path::PathBuf;
use strum_macros::{Display, EnumString};

#[derive(Debug, EnumString, Display, Clone, Copy, PartialEq, Eq, Hash)]
#[strum(serialize_all = "kebab-case")]
pub(in crate::options) enum ParseFileGroup {
    Audio,
    Video,
    Signs,
    #[strum(serialize = "subs")]
    #[strum(serialize = "subtitles")]
    Subs,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub(in crate::options) enum TargetKind {
    Group(ParseFileGroup),
    Path(PathBuf),
}

#[derive(Debug)]
pub(in crate::options) struct Raw {
    pub call_tool: Option<(Tool, Vec<OsString>)>,
    pub untarget: Vec<OsString>,
    pub target: HashMap<TargetKind, Vec<OsString>>,
}

impl Raw {
    pub fn new() -> Self {
        let args: Vec<OsString> = env::args_os().skip(1).collect();
        Self::new_from_args(args)
    }

    fn new_from_args(args: Vec<OsString>) -> Self {
        let mut call_tool: Option<(Tool, Vec<OsString>)> = None;
        let mut untarget: Vec<OsString> = Vec::new();
        let mut target: HashMap<TargetKind, Vec<OsString>> = HashMap::new();
        let mut current_target: Option<TargetKind> = None;

        let mut i = 0;
        while i < args.len() {
            let arg = &args[i];
            let s = arg.to_string_lossy();

            if s.starts_with("--") {
                let maybe_tool = &s[2..];
                if let Ok(tool) = maybe_tool.parse::<Tool>() {
                    let rest = args[i + 1..].to_vec();
                    call_tool = Some((tool, rest));
                    break;
                }
            }

            match s.as_ref() {
                "--target" | "-t" => {
                    i += 1;
                    if i < args.len() {
                        let target_str = args[i].to_string_lossy();
                        if target_str == "global" {
                            current_target = None;
                        } else {
                            let key = if let Ok(group) = target_str.parse::<ParseFileGroup>() {
                                TargetKind::Group(group)
                            } else {
                                let path = PathBuf::from(args[i].clone());
                                if path.exists() {
                                    TargetKind::Path(path.canonicalize().unwrap_or(path))
                                } else {
                                    TargetKind::Path(path)
                                }
                            };
                            current_target = Some(key.clone());
                            target.entry(key).or_insert_with(Vec::new);
                        }
                    }
                }
                _ => {
                    if let Some(trg) = &current_target {
                        target.get_mut(trg).unwrap().push(arg.clone());
                    } else {
                        untarget.push(arg.clone());
                    }
                }
            }

            i += 1;
        }

        Self {
            call_tool,
            untarget,
            target,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn oss(args: &[&str]) -> Vec<OsString> {
        args.iter().map(|s| OsString::from(s)).collect()
    }

    fn run_with_args(args: &[&str]) -> Raw {
        Raw::new_from_args(oss(args))
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

        assert_eq!(raw.untarget, oss(&["arg1", "arg2", "--g1", "--g2"]));

        assert_eq!(
            raw.target
                .get(&TargetKind::Group(ParseFileGroup::Video))
                .unwrap(),
            &oss(&["--opt1", "--opt2"])
        );

        assert_eq!(
            raw.target
                .get(&TargetKind::Group(ParseFileGroup::Audio))
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

        let target_key = TargetKind::Path(PathBuf::from("some/folder"));

        assert!(raw.target.contains_key(&target_key));
        assert_eq!(raw.target.get(&target_key).unwrap(), &oss(&["--x", "--y"]));
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
            raw.target
                .get(&TargetKind::Group(ParseFileGroup::Subs))
                .unwrap(),
            &oss(&["--opt_sub", "--opt_s"])
        );
    }

    #[test]
    fn only_tool() {
        let raw = run_with_args(&["--mkvextract", "file.mkv"]);

        assert!(raw.untarget.is_empty());
        assert!(raw.target.is_empty());
        assert_eq!(raw.call_tool, Some((Tool::Mkvextract, oss(&["file.mkv"]))));
    }
}
