use crate::types::AppError;

pub trait TryInit {
    fn try_init() -> Result<Self, AppError>
    where
        Self: Sized;
}
