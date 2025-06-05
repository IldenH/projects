use quick_xml::de::from_str;
use serde::Deserialize;
use std::fs::read_to_string;

#[derive(Debug, Deserialize)]
struct Data {
    name: String,
    age: i32,
}

fn main() {
    // let xml = r#"<Data><name>Alice</name><age>30</age></Data>"#;
    let xml = read_to_string("file.xml").unwrap();
    let data: Data = from_str(&xml).unwrap();
    dbg!(data);
}
