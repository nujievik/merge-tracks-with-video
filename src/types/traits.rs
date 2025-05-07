pub(in crate::types) trait ClapArgID {
    type Arg;
    fn as_str(arg: Self::Arg) -> &'static str;
}

pub(in crate::types) trait OffOnPro {
    fn off_on_pro(self, pro: bool) -> Self;
}
