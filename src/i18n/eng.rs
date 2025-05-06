use super::Msg;

pub(super) fn eng(msg: Msg) -> String {
    match msg {
        Msg::FailGetStartDir => "Failed to get start directory".to_string(),
        Msg::FailGetOut => "Failed to get output".to_string(),
        Msg::FailInitPatterns { s } => format!("Failed to init {} patterns", s),
        Msg::FailCheckPkg { s, s1 } => format!(
            "'{}' from package '{}' is not installed. Please install it, add to system PATH and re-run.",
            s, s1
        ),
        Msg::FailWriteJson { s } => format!(
            "Failed to write command to JSON: {}. Using CLI (may fail if command is too long)",
            s
        ),
        Msg::ExeCommand => "Executing command".to_string(),
        Msg::FieldNotHasLim { s } => format!("Field '{}' not has default limit. Sets 0", s),
    }
}
