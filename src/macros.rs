#[macro_export]
macro_rules! val_from_matches {
    // Case 1: Default function returns plain value
    ($matches:ident, $typ:ty, $arg:expr, $default_fn:expr) => {
        match $matches
            .try_remove_one::<$typ>(Self::as_str($arg))
            .map_err(AppError::from)?
        {
            Some(val) => val,
            None => $default_fn(),
        }
    };

    // Case 2: Default function returns Result
    ($matches:ident, $typ:ty, $arg:expr, $default_fn:expr, try_default) => {
        match $matches
            .try_remove_one::<$typ>(Self::as_str($arg))
            .map_err(AppError::from)?
        {
            Some(val) => val,
            None => $default_fn().map_err(AppError::from)?,
        }
    };

    // Case 3: Return Option<T>
    ($matches:ident, $typ:ty, $arg:expr, @no_default) => {
        $matches
            .try_remove_one::<$typ>(Self::as_str($arg))
            .map_err(AppError::from)?
    };

    // Case 4: Off on pro flag logic
    ($matches:ident, $typ:ty, $arg:expr, $no_arg:expr, @off_on_pro) => {
        match $matches
            .try_remove_one::<$typ>(Self::as_str($arg))
            .map_err(AppError::from)?
        {
            Some(true) => Some(true),
            _ => {
                match $matches
                    .try_remove_one::<$typ>(Self::as_str($no_arg))
                    .map_err(AppError::from)?
                {
                    Some(true) => Some(false),
                    _ => None,
                }
            }
        }
    };
}
