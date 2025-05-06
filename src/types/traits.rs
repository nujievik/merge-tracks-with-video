pub(super) trait ClapArgID {
    type Arg;
    fn as_str(arg: Self::Arg) -> &'static str;
}
