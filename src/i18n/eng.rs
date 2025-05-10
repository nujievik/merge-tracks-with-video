use super::Msg;

pub(super) fn eng(msg: Msg) -> String {
    match msg {
        Msg::ExeCommand => "Executing command".to_string(),
        Msg::FailCreateThdPool => {
            "Failed to create limited thread pool (using default)".to_string()
        }
        Msg::FailSetPaths { s, s1 } => format!(
            "'{}' from package '{}' is not installed. Please install it, add to system PATH and re-run",
            s, s1
        ),
        Msg::FailWriteJson { s } => format!(
            "Failed to write command to JSON: {}. Using CLI (may fail if command is too long)",
            s
        ),
        Msg::NoInputFiles => "No track files found in the input directory".to_string(),
        Msg::UnsupLngLog { s, s1 } => format!(
            "Language '{}' is not supported for logging. Using '{}'",
            s, s1
        ),
    }
}
