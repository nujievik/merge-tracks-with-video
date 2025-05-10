use crate::types::AppError;

pub trait TryInit {
    fn try_init() -> Result<Self, AppError>
    where
        Self: Sized;
}

pub trait ClapArgID {
    type Arg;
    fn as_str(arg: Self::Arg) -> &'static str;
}

pub trait OffOnPro {
    fn off_on_pro(self, pro: bool) -> Self;
}
