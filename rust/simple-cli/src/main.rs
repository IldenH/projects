use serde::Deserialize;
use std::fs::read_to_string;

#[derive(Deserialize, Debug)]
struct Config {
    is_yellow: bool,
    stuff: Stuff,
}

#[derive(Deserialize, Debug)]
struct Stuff {
    yes: u32,
}

fn main() {
    let config_file = read_to_string("config.toml").unwrap();
    let config: Config = toml::from_str(&config_file).unwrap();
    // dbg!(config);

    if config.is_yellow {
        println!("Yellow!")
    }
}
