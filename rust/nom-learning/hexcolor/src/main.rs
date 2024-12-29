// mostly just trying to understand the example on https://crates.io/crates/nom by writing whilst
// reading and playing with the docs

use nom::{
    bytes::complete::{tag, take_while_m_n},
    character::complete::digit1,
    combinator::map_res,
    sequence::tuple,
    IResult,
};

#[derive(Debug, PartialEq)]
pub struct Color {
    pub red: u8,
    pub green: u8,
    pub blue: u8,
}

fn from_hex(input: &str) -> Result<u8, std::num::ParseIntError> {
    u8::from_str_radix(input, 16)
}

fn is_hexdigit(c: char) -> bool {
    c.is_ascii_hexdigit()
}

fn parser(input: &str) -> IResult<&str, u8> {
    map_res(digit1, str::parse)(input)
}

fn hex_primary(input: &str) -> IResult<&str, u8> {
    // map_res(take_while_m_n(2, 2, is_hexdigit), from_hex)(input)
    map_res(
        take_while_m_n(2, 2, |c: char| c.is_ascii_hexdigit()),
        from_hex,
    )(input)
}

fn hex_color(input: &str) -> IResult<&str, Color> {
    let (input, _) = tag("#")(input)?;
    let (input, (red, green, blue)) = tuple((hex_primary, hex_primary, hex_primary))(input)?;

    Ok((input, Color { red, green, blue }))
}

fn main() {
    #![allow(unused_must_use)]
    dbg!(parser("2112"));
    dbg!(hex_primary("1045"));
    dbg!(hex_color("#432f1a"));
}

#[test]
fn parse_color() {
    let color = Color {
        red: 10,
        green: 10,
        blue: 10,
    };

    let color2 = Color {
        red: 10,
        green: 10,
        blue: 10,
    };

    assert_eq!(color, color2);
}
