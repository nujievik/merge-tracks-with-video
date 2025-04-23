use std::str::FromStr;

#[derive(Clone)]
pub struct RangeMux {
    pub start: u32,
    pub end: u32,
}

impl FromStr for RangeMux {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let trimmed = s.trim();

        let (start, end) = match Self::detect_delimiter(trimmed) {
            Some((delimiter, count)) if count > 1 => {
                return Err(format!(
                    "Too many '{}' delimiters in input: '{}'",
                    delimiter, s
                ));
            }
            Some((delimiter, _)) => Self::parse_with_delimiter(trimmed, delimiter)?,
            None => Self::parse_single_or_empty(trimmed)?,
        };

        Ok(RangeMux { start, end })
    }
}

impl RangeMux {
    pub fn new() -> Self {
        Self {
            start: 0,
            end: u32::MAX,
        }
    }

    fn detect_delimiter(s: &str) -> Option<(&str, usize)> {
        for delimiter in &[",", "-", ".."] {
            if s.contains(delimiter) {
                return Some((delimiter, s.matches(delimiter).count()));
            }
        }
        None
    }

    fn parse_with_delimiter(s: &str, delimiter: &str) -> Result<(u32, u32), String> {
        let parts: Vec<&str> = s.splitn(2, delimiter).collect();

        let start = parts.get(0).copied().unwrap_or("").trim();
        let end = parts.get(1).copied().unwrap_or("").trim();

        let start = Self::parse_part(start, 0)?;
        let end = Self::parse_part(end, u32::MAX)?;

        if end < start {
            return Err(format!(
                "End of range ({end}) must be greater than or equal to start ({start})"
            ));
        }

        Ok((start, end))
    }

    fn parse_single_or_empty(s: &str) -> Result<(u32, u32), String> {
        if s.is_empty() {
            Ok((0, u32::MAX))
        } else {
            let start = Self::parse_part(s, 0)?;
            Ok((start, u32::MAX))
        }
    }

    fn parse_part(part: &str, default: u32) -> Result<u32, String> {
        if part.is_empty() {
            Ok(default)
        } else {
            part.parse::<u32>()
                .map_err(|_| format!("Invalid number: '{}'", part))
        }
    }
}
