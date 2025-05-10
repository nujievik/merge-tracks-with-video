use clap::parser::MatchesError;

#[derive(Debug)]
pub enum AppErrorKind {
    InvalidValue,
    MatchesErrorDowncast,
    MatchesErrorUnknownArgument,
    Unknown,
}

impl Default for AppErrorKind {
    fn default() -> Self {
        Self::Unknown
    }
}

#[derive(Debug)]
pub struct AppError {
    pub message: Option<String>,
    pub code: i32,
    pub kind: AppErrorKind,
}

impl std::fmt::Display for AppError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match &self.message {
            Some(msg) => write!(f, "{}", msg),
            None => write!(f, ""),
        }
    }
}

impl std::error::Error for AppError {}

impl AppError {
    pub fn new() -> Self {
        Self {
            message: None,
            code: 1,
            kind: AppErrorKind::default(),
        }
    }

    pub fn ok() -> Self {
        Self::new().code(0)
    }

    pub fn from_any<E: std::error::Error>(err: E) -> Self {
        Self::new().message(err)
    }

    pub fn message(mut self, msg: impl ToString) -> Self {
        self.message = Some(msg.to_string());
        self
    }

    pub fn code(mut self, code: i32) -> Self {
        self.code = code;
        self
    }

    fn kind(mut self, kind: AppErrorKind) -> Self {
        self.kind = kind;
        self
    }

    pub fn use_stderr(&self) -> bool {
        self.code != 0
    }

    pub fn print(&self) {
        if let Some(msg) = &self.message {
            if self.use_stderr() {
                eprintln!("{}", msg);
            } else {
                println!("{}", msg);
            }
        }
    }
}

impl From<String> for AppError {
    fn from(s: String) -> Self {
        Self::new().message(s)
    }
}

impl From<&str> for AppError {
    fn from(s: &str) -> Self {
        Self::new().message(s)
    }
}

impl From<clap::Error> for AppError {
    fn from(err: clap::Error) -> Self {
        let _ = err.print();
        Self::new().code(err.exit_code())
    }
}

impl From<AppError> for clap::Error {
    fn from(err: AppError) -> Self {
        let mut msg = err.to_string();
        if !msg.ends_with('\n') {
            msg.push('\n');
        }
        clap::Error::raw(clap::error::ErrorKind::InvalidValue, msg)
    }
}

impl From<MatchesError> for AppError {
    fn from(err: MatchesError) -> Self {
        Self::new().message(&err).kind(match err {
            MatchesError::Downcast { .. } => AppErrorKind::MatchesErrorDowncast,
            MatchesError::UnknownArgument { .. } => AppErrorKind::MatchesErrorUnknownArgument,
            _ => AppErrorKind::Unknown,
        })
    }
}

impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        Self::from_any(err)
    }
}
