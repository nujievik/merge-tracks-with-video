use mux_media::types::RangeU32;
use std::str::FromStr;

#[test]
fn test_new() {
    let range = RangeU32::new();
    assert_eq!(0, range.start);
    assert_eq!(u32::MAX, range.end);
}

#[test]
fn test_from_str() {
    for s in &[
        "", "5", "0", " 10 ", "5,10", "5,", ",10", "5-10", "5-", "-10", "5..10",
    ] {
        assert!(RangeU32::from_str(s).is_ok());
    }
}

#[test]
fn test_err_from_str() {
    for s in &["a,10", "5,b", "5,10,15", "5-10-15", "5.10", "10,5"] {
        assert!(RangeU32::from_str(s).is_err());
    }
}

#[test]
fn test_expected_start_end() {
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

#[test]
fn test_expected_err_messages() {
    let cases = [
        ("x", "invalid digit"),
        ("1-x", "invalid digit"),
        ("1,,8", "Too many ',' delimiters in input"),
        (
            "8-1",
            "End of range (1) must be greater than or equal to start (8)",
        ),
    ];

    for (input, expected_msg) in &cases {
        match RangeU32::from_str(input) {
            Err(e) => assert!(
                e.to_string().contains(expected_msg),
                "Expected error contains '{}' for input '{}', but got '{}'",
                expected_msg,
                input,
                e.to_string(),
            ),
            Ok(_) => panic!("Expected error for input '{}', but got Ok", input),
        }
    }
}
