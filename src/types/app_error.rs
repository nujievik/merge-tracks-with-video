use std::error::Error;
use std::fmt;

#[derive(Debug)]
pub struct AppError {
    pub message: Option<String>,
    pub code: i32,
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match &self.message {
            Some(msg) => write!(f, "[Error {}] {}", self.code, msg),
            None => write!(f, "[Error {}]", self.code),
        }
    }
}

impl Error for AppError {}

impl From<String> for AppError {
    fn from(s: String) -> Self {
        Self {
            message: Some(s),
            code: 1,
        }
    }
}

impl From<&str> for AppError {
    fn from(s: &str) -> Self {
        Self {
            message: Some(s.to_string()),
            code: 1,
        }
    }
}

impl AppError {
    pub fn new() -> Self {
        Self {
            message: None,
            code: 1,
        }
    }

    pub fn ok() -> Self {
        Self {
            message: None,
            code: 0,
        }
    }

    pub fn message(mut self, msg: impl ToString) -> Self {
        self.message = Some(msg.to_string());
        self
    }

    pub fn from_any<E: std::error::Error>(err: E) -> Self {
        Self {
            message: Some(err.to_string()),
            code: 1,
        }
    }
}

impl From<clap::Error> for AppError {
    fn from(e: clap::Error) -> Self {
        let _ = e.print();
        if e.use_stderr() {
            Self::new()
        } else {
            Self::ok()
        }
    }
}
