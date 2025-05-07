use crate::i18n::Msg;
use crate::traits::TryInit;
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

impl Tool {
    fn is_mkvtoolnix(&self) -> bool {
        self != &Self::Ffprobe
    }

    fn iter_mkvtoolnix() -> impl Iterator<Item = Self> {
        vec![Self::Mkvextract, Self::Mkvinfo, Self::Mkvmerge].into_iter()
    }

    fn to_str_package(&self) -> &'static str {
        if self.is_mkvtoolnix() {
            "mkvtoolnix"
        } else {
            "ffmpeg"
        }
    }
}

pub struct Tools {
    paths: Option<HashMap<Tool, PathBuf>>,
    json: Option<PathBuf>,
}

impl Tools {
    pub fn new() -> Self {
        Self {
            paths: None,
            json: None,
        }
    }

    pub fn try_set_paths(
        mut self,
        tools: impl IntoIterator<Item = Tool>,
    ) -> Result<Self, AppError> {
        for tool in tools {
            if let Some(path) = Self::get_path(tool) {
                self.paths
                    .get_or_insert_with(HashMap::new)
                    .insert(tool, path);
            } else {
                return Err(AppError::from(
                    Msg::FailSetPaths {
                        s: tool.as_ref(),
                        s1: tool.to_str_package(),
                    }
                    .get(),
                ));
            }
        }

        Ok(self)
    }

    pub fn json(mut self, json: impl Into<PathBuf>) -> Self {
        self.json = Some(json.into());
        self
    }

    fn get_path(tool: Tool) -> Option<PathBuf> {
        let tool_str = tool.as_ref();
        let mut potential_paths = vec![PathBuf::from(tool_str)];

        if cfg!(target_os = "windows") && tool.is_mkvtoolnix() {
            for dir in &[
                "C:\\Program Files\\MkvToolNix",
                "C:\\Program Files (x86)\\MkvToolNix",
            ] {
                let mut path = PathBuf::from(dir);
                path.push(tool_str);
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

    pub fn execute<I, T>(&self, tool: Tool, args: I, msg: Option<&str>) -> Result<String, AppError>
    where
        I: IntoIterator<Item = T> + Clone,
        T: AsRef<OsStr>,
    {
        if let Some(msg) = msg {
            debug!("{}", msg);
        }

        let mut command = Command::new(
            self.paths
                .as_ref()
                .and_then(|paths| paths.get(&tool))
                .map(|p| p.as_path())
                .unwrap_or_else(|| Path::new(tool.as_ref())),
        );

        let use_json = self.json.is_some() && tool.is_mkvtoolnix();

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
            Ok(output) => Err(AppError::from(
                String::from_utf8_lossy(&output.stdout).to_string(),
            )),
            Err(e) => Err(AppError::from(format!("Execution error: {}", e))),
        }
    }
}

impl TryInit for Tools {
    fn try_init() -> Result<Self, AppError> {
        let tools = Self::new().try_set_paths(Tool::iter_mkvtoolnix())?;
        Ok(tools)
    }
}
