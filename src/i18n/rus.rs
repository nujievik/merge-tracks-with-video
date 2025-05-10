use super::Msg;

pub(super) fn rus(msg: Msg) -> String {
    match msg {
        Msg::ExeCommand => "Выполнение команды".to_string(),
        Msg::FailCreateThdPool => {
            "Не удалось лимитировать количество потоков (используем дефолтное)".to_string()
        }
        Msg::FailSetPaths { s, s1 } => format!(
            "'{}' из пакета '{}' не установлен. Пожалуйста, установите его, добавьте в системный PATH и перезапустите",
            s, s1
        ),
        Msg::FailWriteJson { s } => format!(
            "Не удалось записать команду в JSON: {}. Используем CLI (может привести к ошибке, если команда слишком длинная)",
            s
        ),
        Msg::NoInputFiles => "Не найдены файлы с треками во входящей директории".to_string(),
        Msg::UnsupLngLog { s, s1 } => format!(
            "Язык '{}' не поддерживается для ведения журнала. Используем '{}'",
            s, s1
        ),
    }
}
