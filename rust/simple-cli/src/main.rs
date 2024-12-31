use clap::Command;
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

fn cli() -> Command {
    Command::new("simple")
        .about("A simple cli")
        .subcommand_required(true)
        .arg_required_else_help(true)
        .subcommand(Command::new("config").about("Shows info about config"))
}

fn main() {
    let matches = cli().get_matches();

    match matches.subcommand() {
        Some(("config", _)) => print_config(),
        _ => unreachable!(),
    };
}

fn print_config() {
    let config_file = read_to_string("config.toml").unwrap();
    let config: Config = toml::from_str(&config_file).unwrap();

    if config.is_yellow {
        println!("Yellow!")
    }
    println!("yes: {}", config.stuff.yes)
}
