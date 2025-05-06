mod base_impls;
pub(super) mod from_arg_matches;
mod id;

use id::AttachID;
use std::collections::HashSet;

#[derive(Clone)]
pub struct Attachs {
    pub fonts: BaseAttachsFields,
    pub other: BaseAttachsFields,
}

#[derive(Clone)]
pub struct BaseAttachsFields {
    pub no_flag: bool,
    pub inverse: bool,
    pub ids_hashed: Option<HashSet<AttachID>>,
    pub ids_unhashed: Option<Vec<AttachID>>,
}
