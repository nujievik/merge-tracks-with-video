use colored::*;
use std::collections::{BTreeMap, HashSet};
use std::ffi::{OsStr, OsString};
use std::fs::File;
use std::io::BufWriter;
use std::path::{Path, PathBuf};
use std::process::Command;
use strum_macros::{Display, EnumIter, EnumString};

#[derive(Debug)]
pub struct ToolExeParams<'a> {
    pub message: &'a str,
    pub json: Option<PathBuf>,
    pub verbose: bool,
}

impl<'a> ToolExeParams<'a> {
    pub fn new() -> Self {
        Self {
            message: "",
            json: None,
            verbose: false,
        }
    }
}

#[derive(
    Display, EnumIter, EnumString, Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord,
)]
#[strum(serialize_all = "kebab-case")]
pub enum Tool {
    Ffprobe,
    Mkvextract,
    Mkvinfo,
    Mkvmerge,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum ToolPackage {
    Ffmpeg,
    Mkvtoolnix,
}

impl ToolPackage {
    pub fn tools(&self) -> &'static [Tool] {
        match self {
            ToolPackage::Ffmpeg => &[Tool::Ffprobe],
            ToolPackage::Mkvtoolnix => &[Tool::Mkvextract, Tool::Mkvinfo, Tool::Mkvmerge],
        }
    }

    pub fn all() -> impl Iterator<Item = ToolPackage> {
        [ToolPackage::Ffmpeg, ToolPackage::Mkvtoolnix].into_iter()
    }
}

pub struct Tools<'a> {
    packages: BTreeMap<ToolPackage, HashSet<Tool>>,
    paths: BTreeMap<Tool, PathBuf>,
    params: ToolExeParams<'a>,
}

impl<'a> Tools<'a> {
    fn get_path(tool: Tool, is_mkvtoolnix: bool) -> Option<PathBuf> {
        let tool_name = tool.to_string();
        let mut potential_paths = vec![PathBuf::from(&tool_name)];

        if is_mkvtoolnix && cfg!(target_os = "windows") {
            for dir in &[
                "C:\\Program Files\\MkvToolNix",
                "C:\\Program Files (x86)\\MkvToolNix",
            ] {
                let mut path = PathBuf::from(dir);
                path.push(&tool_name);
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

    pub fn new() -> Self {
        let mut packages = BTreeMap::new();
        let mut paths = BTreeMap::new();

        for package in ToolPackage::all() {
            let tools: HashSet<_> = package.tools().iter().cloned().collect();
            for &tool in &tools {
                if let Some(path) = Self::get_path(tool, package == ToolPackage::Mkvtoolnix) {
                    paths.insert(tool, path);
                }
            }
            packages.insert(package, tools);
        }

        Self {
            packages,
            paths,
            params: ToolExeParams::new(),
        }
    }

    pub fn check_package(&self, package: ToolPackage) {
        if let Some(tools) = self.packages.get(&package) {
            for &tool in tools {
                if !self.paths.contains_key(&tool) {
                    eprintln!(
                        "{} '{}' from package '{:?}' is not installed. Please install it and \
add to system PATH.",
                        "Error:".red(),
                        tool,
                        package
                    );
                    std::process::exit(1);
                }
            }
        } else {
            eprintln!(
                "{} package '{:?}' is not included in tools.",
                "Warning:".yellow(),
                package
            );
        }
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
                    .ok_or_else(|| "Unsupported UTF-8 symbol in argument.".to_string())
                    .map(|s| s.to_string())
            })
            .collect::<Result<Vec<String>, _>>()?;

        let file = File::create(json).map_err(|e| format!("File create error: {}", e))?;
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &args)
            .map_err(|e| format!("JSON write error: {}", e))?;

        Ok(args)
    }

    fn get_command<I, T>(
        &self,
        tool: Tool,
        args: I,
        params: &ToolExeParams,
    ) -> (Command, Option<Vec<String>>)
    where
        I: IntoIterator<Item = T> + Clone,
        T: AsRef<OsStr>,
    {
        let mut command = match self.paths.get(&tool) {
            Some(tool_path) => Command::new(tool_path),
            None => Command::new(tool.to_string()),
        };

        let is_mkvtoolnix = self
            .packages
            .get(&ToolPackage::Mkvtoolnix)
            .map_or(false, |tools| tools.contains(&tool));
        let use_json = is_mkvtoolnix && params.json.is_some();

        if use_json {
            let json = params.json.as_ref().unwrap();

            match Self::write_args_to_json(args.clone(), json) {
                Ok(args) => {
                    let mut json_with_at = OsString::from("@");
                    json_with_at.push(json);
                    command.arg(json_with_at);
                    return (command, Some(args));
                }
                Err(e) => {
                    eprintln!(
                        "{} Failed to write command arguments to JSON: {} Falling back to \
passing arguments via command line.",
                        "Warning:".yellow(),
                        e,
                    );
                    command.args(args);
                }
            }
        } else {
            command.args(args);
        }

        (command, None)
    }

    fn print_verbose_messages(
        command: &Command,
        args: Option<Vec<String>>,
        params: &ToolExeParams,
    ) {
        if !params.message.is_empty() {
            println!("{}", params.message);
        }

        println!("Executing the following command:\n{:?}", command);

        if let Some(args) = args {
            let args_str = args.join("\" \"");
            println!("JSON arguments: \"{}\"", args_str);
        }
    }

    pub fn execute<I, T>(
        &self,
        tool: Tool,
        args: I,
        params: Option<&ToolExeParams>,
    ) -> Result<String, String>
    where
        I: IntoIterator<Item = T> + Clone,
        T: AsRef<OsStr>,
    {
        let params = params.unwrap_or(&self.params);

        let (mut command, args) = self.get_command(
            tool,
            if params.verbose { args.clone() } else { args },
            params,
        );

        if params.verbose {
            Self::print_verbose_messages(&command, args, params);
        }

        match command.output() {
            Ok(output) if output.status.success() => {
                Ok(String::from_utf8_lossy(&output.stdout).to_string())
            }
            Ok(output) => Err(format!(
                "Error: {}",
                String::from_utf8_lossy(&output.stdout).to_string()
            )),
            Err(e) => Err(format!("Error executing command: {}", e)),
        }
    }
}
