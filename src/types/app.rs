use std::error::Error;
use std::fmt;

#[macro_export]
macro_rules! unwrap_or_return {
    ($expr:expr) => {
        match $expr {
            AppFlow::Proceed(val) => val,
            AppFlow::Done => return AppFlow::Done,
            AppFlow::Fail(e) => return AppFlow::Fail(e),
        }
    };
}

pub enum AppFlow<T> {
    Proceed(T),
    Done,
    Fail(Box<dyn Error + Send + Sync>),
}

impl<T> AppFlow<T> {
    pub fn from_result<E>(res: Result<T, E>) -> Self
    where
        E: Into<Box<dyn Error + Send + Sync>>,
    {
        match res {
            Ok(val) => Self::Proceed(val),
            Err(e) => Self::Fail(e.into()),
        }
    }

    pub fn from_fail_str<S: Into<String>>(s: S) -> Self {
        Self::Fail(Box::new(AppError::from(s.into())))
    }
}

impl<T, E> From<E> for AppFlow<T>
where
    E: Into<Box<dyn std::error::Error + Send + Sync>>,
{
    fn from(e: E) -> Self {
        AppFlow::Fail(e.into())
    }
}

#[derive(Debug)]
pub struct AppError(String);

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl Error for AppError {}

impl From<String> for AppError {
    fn from(s: String) -> Self {
        AppError(s)
    }
}

impl From<&str> for AppError {
    fn from(s: &str) -> Self {
        AppError(s.to_string())
    }
}
