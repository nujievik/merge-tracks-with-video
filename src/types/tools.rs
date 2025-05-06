use crate::i18n::Msg;
use crate::types::AppError;
use log::{debug, warn};
use std::collections::HashMap;
use std::ffi::{OsStr, OsString};
use std::fs::File;
use std::io::BufWriter;
use std::path::{Path, PathBuf};
use std::process::Command;
use strum_macros::{AsRefStr, EnumString};

#[derive(AsRefStr, EnumString, Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[strum(serialize_all = "kebab-case")]
pub enum Tool {
    Ffprobe,
    Mkvextract,
    Mkvinfo,
    Mkvmerge,
}

#[derive(AsRefStr, PartialEq)]
#[strum(serialize_all = "kebab-case")]
pub enum ToolPkg {
    Ffmpeg,
    Mkvtoolnix,
}

impl ToolPkg {
    pub fn tools(&self) -> &'static [Tool] {
        match self {
            ToolPkg::Ffmpeg => &[Tool::Ffprobe],
            ToolPkg::Mkvtoolnix => &[Tool::Mkvextract, Tool::Mkvinfo, Tool::Mkvmerge],
        }
    }

    pub fn all() -> impl Iterator<Item = ToolPkg> {
        [ToolPkg::Ffmpeg, ToolPkg::Mkvtoolnix].into_iter()
    }
}

pub struct Tools {
    paths: HashMap<Tool, PathBuf>,
    json: Option<PathBuf>,
}

impl Tools {
    pub fn new() -> Self {
        let mut paths = HashMap::new();

        for package in ToolPkg::all() {
            for &tool in package.tools() {
                if let Some(path) = Self::get_path(tool, package == ToolPkg::Mkvtoolnix) {
                    paths.insert(tool, path);
                }
            }
        }

        Self { paths, json: None }
    }

    pub fn json(mut self, json: impl Into<PathBuf>) -> Self {
        self.json = Some(json.into());
        self
    }

    pub fn check_pkg(&self, pkg: ToolPkg) -> Result<(), AppError> {
        for &tool in pkg.tools() {
            if !self.paths.contains_key(&tool) {
                let msg = Msg::FailCheckPkg {
                    s: tool.as_ref(),
                    s1: pkg.as_ref(),
                };
                return Err(AppError::from(msg.get()));
            }
        }
        Ok(())
    }

    fn get_path(tool: Tool, is_mkvtoolnix: bool) -> Option<PathBuf> {
        let tool = tool.as_ref();
        let mut potential_paths = vec![PathBuf::from(tool)];

        if is_mkvtoolnix && cfg!(target_os = "windows") {
            for dir in &[
                "C:\\Program Files\\MkvToolNix",
                "C:\\Program Files (x86)\\MkvToolNix",
            ] {
                let mut path = PathBuf::from(dir);
                path.push(tool);
                path.set_extension("exe");
                potential_paths.push(path);
            }
        }

        potential_paths.into_iter().find(|path| {
            Command::new(path)
                .arg("-h")
                .output()
                .map(|o| o.status.success())
                .unwrap_or(false)
        })
    }

    fn write_args_to_json<I, T>(args: I, json: &Path) -> Result<Vec<String>, String>
    where
        I: IntoIterator<Item = T> + Clone,
        T: AsRef<OsStr>,
    {
        let args = args
            .into_iter()
            .map(|arg| {
                arg.as_ref()
                    .to_str()
                    .ok_or_else(|| "Unsupported UTF-8 symbol.".to_string())
                    .map(|s| s.to_string())
            })
            .collect::<Result<Vec<_>, _>>()?;

        let file = File::create(json).map_err(|e| format!("Create error: {}", e))?;
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &args)
            .map_err(|e| format!("JSON write error: {}", e))?;

        Ok(args)
    }

    pub fn execute<I, T>(&self, tool: Tool, args: I, msg: Option<&str>) -> Result<String, String>
    where
        I: IntoIterator<Item = T> + Clone,
        T: AsRef<OsStr>,
    {
        if let Some(msg) = msg {
            debug!("{}", msg);
        }

        let mut command = match self.paths.get(&tool) {
            Some(path) => Command::new(path),
            None => Command::new(tool.as_ref()),
        };

        let use_json = self.json.is_some()
            && matches!(tool, Tool::Mkvmerge | Tool::Mkvinfo | Tool::Mkvextract);

        let args_json = if use_json {
            let json = self.json.as_deref().unwrap_or(Path::new(".command.json"));
            match Self::write_args_to_json(args.clone(), json) {
                Ok(vec) => {
                    let mut json_with_at = OsString::from("@");
                    json_with_at.push(json);
                    command.arg(json_with_at);
                    Some(vec)
                }
                Err(e) => {
                    warn!("{}", Msg::FailWriteJson { s: &e }.get());
                    command.args(args);
                    None
                }
            }
        } else {
            command.args(args);
            None
        };

        debug!("{}:\n{:?}", Msg::ExeCommand.get(), command);
        if let Some(args) = &args_json {
            debug!("Args in JSON:\n{:?}", args);
        }

        match command.output() {
            Ok(output) if output.status.success() => {
                Ok(String::from_utf8_lossy(&output.stdout).to_string())
            }
            Ok(output) => Err(String::from_utf8_lossy(&output.stdout).to_string()),
            Err(e) => Err(format!("Execution error: {}", e)),
        }
    }
}
