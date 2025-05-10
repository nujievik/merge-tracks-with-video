use super::{Tracks, TracksFlags, TracksLangs, TracksNames};
use crate::traits::OffOnPro;

impl OffOnPro for Tracks {
    fn off_on_pro(mut self, pro: bool) -> Self {
        if pro {
            self.flags = TracksFlags::off_on_pro(self.flags, pro);
            self.names = TracksNames::off_on_pro(self.names, pro);
            self.langs = TracksLangs::off_on_pro(self.langs, pro);
        };

        self
    }
}

impl OffOnPro for TracksFlags {
    fn off_on_pro(mut self, pro: bool) -> Self {
        if pro {
            if self.defaults.add.is_none() {
                self.defaults.add = Some(false);
            }
            if self.forceds.add.is_none() {
                self.forceds.add = Some(false);
            }
            if self.enableds.add.is_none() {
                self.enableds.add = Some(false);
            }
        };

        self
    }
}

impl OffOnPro for TracksNames {
    fn off_on_pro(mut self, pro: bool) -> Self {
        if pro && self.add.is_none() {
            self.add = Some(false);
        }

        self
    }
}

impl OffOnPro for TracksLangs {
    fn off_on_pro(mut self, pro: bool) -> Self {
        if pro && self.add.is_none() {
            self.add = Some(false);
        }

        self
    }
}
