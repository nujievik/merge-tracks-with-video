use mux_media::types::RangeU32;
use std::str::FromStr;

#[test]
fn new() {
    let range = RangeU32::new();
    assert_eq!(0, range.start);
    assert_eq!(u32::MAX, range.end);
}

#[test]
fn from_str() {
    for s in &[
        "", "5", "0", " 10 ", "5,10", "5,", ",10", "5-10", "5-", "-10", "5..10",
    ] {
        assert_eq!(true, RangeU32::from_str(s).is_ok());
    }
}

#[test]
fn err_from_str() {
    for s in &["a,10", "5,b", "5,10,15", "5-10-15", "5.10", "10,5"] {
        assert_eq!(true, RangeU32::from_str(s).is_err());
    }
}

#[test]
fn expected_start_end() {
    let max = u32::MAX;
    let cases = [
        ("", (0, max)),
        (",", (0, max)),
        ("5", (5, max)),
        ("0", (0, max)),
        (" 10 ", (10, max)),
        ("5,10", (5, 10)),
        ("5,", (5, max)),
        (",10", (0, 10)),
        ("5-10", (5, 10)),
        ("5-", (5, max)),
        ("-10", (0, 10)),
        ("6-6", (6, 6)),
        ("3..7", (3, 7)),
    ];

    for (s, expected) in cases {
        match RangeU32::from_str(s) {
            Ok(res) => assert_eq!(
                (res.start, res.end),
                expected,
                "Expected {:?} for input '{}', got {:?}",
                expected,
                s,
                (res.start, res.end)
            ),
            Err(e) => panic!("Unexpected error for input '{}': {}", s, e),
        }
    }
}
