use super::Attachs;
use crate::types::traits::OffOnPro;

impl OffOnPro for Attachs {
    fn off_on_pro(mut self, pro: bool) -> Self {
        if pro && self.sort_fonts.is_none() {
            self.sort_fonts = Some(false);
        };

        self
    }
}
