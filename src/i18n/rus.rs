use super::Msg;

pub(super) fn rus(msg: Msg) -> String {
    match msg {
        Msg::ExeCommand => "Выполнение команды".to_string(),
        Msg::FailSetPaths { s, s1 } => format!(
            "'{}' из пакета '{}' не установлен. Пожалуйста, установите его, добавьте в системный PATH и перезапустите",
            s, s1
        ),
        Msg::FailWriteJson { s } => format!(
            "Ошибка записи команды в JSON: {}. Используем CLI (может привести к ошибке, если команда слишком длинная)",
            s
        ),
    }
}
