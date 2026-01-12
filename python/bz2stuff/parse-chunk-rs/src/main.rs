use chrono::{Datelike, Utc};
use crossbeam::channel::bounded;
use quick_xml::events::Event;
use rayon::prelude::*;
use regex::bytes::Regex;
use std::{
    fs::OpenOptions,
    io::{BufReader, BufWriter, Write},
    thread,
};

const WIKI_FILE: &str = "/BIG/wikipedia/wiki.xml";
const OUTPUT_FILE: &str = "people.csv";

lazy_static::lazy_static! {
    static ref REF_RE: Regex = Regex::new(r"(?s)ref.*").unwrap();
    static ref COMMENT_RE: Regex = Regex::new(r"(?s)<!--.*").unwrap();
    static ref BIRTH_RE: Regex = Regex::new(r"(?m)^\|\s*birth_date\s*=\s*([^\r\n]+)(?:\r?\n|$)").unwrap();
    static ref DEATH_RE: Regex = Regex::new(r"(?m)^\|\s*death_date\s*=\s*([^\r\n]+)(?:\r?\n|$)").unwrap();
    static ref YEAR_RE: Regex = Regex::new(r"\b([1-9][0-9]{2,3})\b").unwrap();
}

struct Page {
    title: Vec<u8>,
    text: Vec<u8>,
}

fn extract_infobox(page: &[u8]) -> Option<&[u8]> {
    let start_pat = b"{{Infobox";
    let start = memchr::memmem::find(page, start_pat)?;

    let mut depth = 0usize;
    let mut i = start;

    let bytes = page;

    while i + 1 < bytes.len() {
        match (&bytes[i], &bytes[i + 1]) {
            (b'{', b'{') => {
                depth += 1;
                i += 2;
            }
            (b'}', b'}') => {
                depth -= 1;
                i += 2;

                if depth == 0 {
                    return Some(&bytes[start..i]);
                }
            }
            _ => i += 1,
        }
    }

    None
}

fn parse_year(s: &[u8]) -> Option<i32> {
    let current_year = Utc::now().year();

    let years: Vec<i32> = YEAR_RE
        .captures_iter(s)
        .filter_map(|caps| {
            let y = std::str::from_utf8(&caps[1]).unwrap().parse::<i32>().ok()?;
            if y >= 100 && y <= current_year {
                Some(y)
            } else {
                None
            }
        })
        .collect();
    return years.get(0).copied();
}

fn process_page(page: &Page) -> Option<String> {
    let infobox = extract_infobox(&page.text)?;

    let birth = BIRTH_RE.captures(infobox)?.get(1)?.as_bytes();
    let birth = &REF_RE.replace_all(birth, b"");

    let death = DEATH_RE.captures(infobox)?.get(1)?.as_bytes();
    let death = &COMMENT_RE.replace_all(death, b"");

    let b = parse_year(birth)?;
    let d = parse_year(death)?;
    let (b, d) = if b > d { (-b, -d) } else { (b, d) };
    if b == d {
        return None;
    };

    let t = String::from_utf8_lossy(&page.title);
    let t = (!t.contains(":")).then_some(t)?;

    Some(format!("{}|{}|{}", t, b, d))
}

fn main() {
    let file = std::fs::File::open(WIKI_FILE).unwrap();
    let reader = BufReader::new(file);

    let (page_tx, page_rx) = bounded::<Page>(256);
    let (line_tx, line_rx) = bounded::<String>(1024);

    let producer = {
        let page_tx = page_tx.clone();
        thread::spawn(move || {
            let mut xml = quick_xml::Reader::from_reader(reader);
            let mut buf = Vec::new();
            let mut title_buf = Vec::new();
            let mut text_buf = Vec::new();
            let mut in_title = false;
            let mut in_text = false;

            loop {
                match xml.read_event_into(&mut buf) {
                    Ok(Event::Start(ref e)) => match e.name().as_ref() {
                        b"title" => {
                            title_buf.clear();
                            in_title = true;
                        }
                        b"text" => {
                            text_buf.clear();
                            in_text = true;
                        }
                        _ => {}
                    },
                    Ok(Event::End(ref e)) => match e.name().as_ref() {
                        b"title" => in_title = false,
                        b"text" => {
                            in_text = false;
                            let page = Page {
                                title: title_buf.clone(),
                                text: text_buf.clone(),
                            };
                            page_tx.send(page).unwrap();
                        }
                        _ => {}
                    },
                    Ok(Event::Text(t)) => {
                        if in_title {
                            title_buf.extend_from_slice(t.as_ref());
                        }
                        if in_text {
                            text_buf.extend_from_slice(t.as_ref());
                        }
                    }
                    Ok(Event::Eof) => break,
                    _ => {}
                }
                buf.clear();
            }
            drop(page_tx);
        })
    };

    let writer = thread::spawn(move || {
        let file = OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(OUTPUT_FILE)
            .unwrap();
        let mut writer = BufWriter::new(file);
        writeln!(writer, "name|birth|death").unwrap();
        for line in line_rx {
            writeln!(writer, "{}", line).unwrap();
        }
        writer.flush().unwrap();
    });

    page_rx
        .into_iter()
        .par_bridge()
        .for_each_with(line_tx.clone(), |line_tx, page| {
            if let Some(person) = process_page(&page) {
                line_tx.send(person).unwrap();
            }
        });

    drop(line_tx);

    producer.join().unwrap();
    writer.join().unwrap();
}
