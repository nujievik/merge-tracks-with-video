use super::Msg;

pub(super) fn rus(msg: Msg) -> String {
    match msg {
        Msg::FailGetStartDir => "Не удалось получить стартовую директорию".to_string(),
        Msg::FailGetOut => "Не удалось получить output".to_string(),
        Msg::FailInitPatterns { s } => format!("Не удалось инициализировать {} паттерны", s),
        Msg::FailCheckPkg { s, s1 } => format!(
            "'{}' из пакета '{}' не установлен. Пожалуйста, установите его, добавьте в системный PATH и перезапустите",
            s, s1
        ),
        Msg::FailWriteJson { s } => format!(
            "Ошибка записи команды в JSON: {}. Используем CLI (может привести к ошибке, если команда слишком длинная)",
            s
        ),
        Msg::ExeCommand => "Выполнение команды".to_string(),
        Msg::FieldNotHasLim { s } => format!(
            "Для поля '{}' не задан лимит по умолчанию. Установлено 0",
            s
        ),
    }
}
