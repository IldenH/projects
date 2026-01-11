use bzip2::read::BzDecoder;
use chrono::{Datelike, Utc};
use memchr::memmem;
use rayon::prelude::*;
use regex::bytes::Regex;
use std::{
    fs::File,
    io::{BufRead, BufReader, BufWriter, Read, Seek, SeekFrom, Write},
    sync::Mutex,
};

fn extract_pages(data: &[u8]) -> Vec<&[u8]> {
    let start_pat = b"<page";
    let end_pat = b"</page>";

    let mut pages = Vec::new();
    let mut pos = 0;

    while let Some(start) = memmem::find(&data[pos..], start_pat) {
        let start_idx = pos + start;

        if let Some(end) = memmem::find(&data[start_idx..], end_pat) {
            let end_idx = start_idx + end + end_pat.len();
            pages.push(&data[start_idx..end_idx]);
            pos = end_idx;
        } else {
            break;
        }
    }

    pages
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

const WIKI_FILE: &str = "/BIG/wikipedia/wiki.xml.bz2";
const INDEX_FILE: &str = "../short_index.txt";
const OUTPUT_FILE: &str = "people.txt";

lazy_static::lazy_static! {
    static ref PAGE_RE: Regex = Regex::new(r"<page.*?>(.*?)</page>").unwrap();
    static ref TITLE_RE: Regex = Regex::new(r"<title.*?>(.*?)</title>").unwrap();
    static ref INFO_RE: Regex = Regex::new(r"\{\{Infobox(.*)\}\}").unwrap();
    static ref BIRTH_RE: Regex = Regex::new(r"\|\s*birth_date\s*=\s*(.*)").unwrap();
    static ref DEATH_RE: Regex = Regex::new(r"\|\s*death_date\s*=\s*(.*)").unwrap();
    static ref YEAR_RE: Regex = Regex::new(r"\b([0-9]{3,4})\b").unwrap();
}

fn parse_year(s: &[u8]) -> Option<i32> {
    if let Some(caps) = YEAR_RE.captures(s) {
        let y = std::str::from_utf8(&caps[1]).ok()?.parse::<i32>().ok()?;
        let current_year = Utc::now().year();
        if y <= current_year {
            return Some(y);
        }
    }
    None
}

fn process_chunk(chunk: (u64, u64), writer: &Mutex<BufWriter<File>>) {
    let (offset, size) = chunk;
    let mut file = File::open(WIKI_FILE).expect("Wiki file missing");
    file.seek(SeekFrom::Start(offset)).unwrap();

    let mut comp = vec![0u8; size as usize];
    file.read_exact(&mut comp).unwrap();

    let mut decoder = BzDecoder::new(&comp[..]);
    let mut data = Vec::new();
    decoder.read_to_end(&mut data).unwrap();

    for page in extract_pages(&data) {
        let block = &page;
        let title = match TITLE_RE.captures(block) {
            Some(c) => c[1].to_vec(),
            None => continue,
        };
        let info = match extract_infobox(block) {
            Some(c) => c.to_vec(),
            None => continue,
        };
        let birth = match BIRTH_RE.captures(&info) {
            Some(c) => c[1].to_vec(),
            None => continue,
        };
        let death = match DEATH_RE.captures(&info) {
            Some(c) => c[1].to_vec(),
            None => continue,
        };

        let birth_year = parse_year(&birth);
        let death_year = parse_year(&death);

        if let Some(b) = birth_year {
            if let Some(d) = death_year {
                let mut w = writer.lock().unwrap();
                let title_str = String::from_utf8_lossy(&title);
                writeln!(w, "{} {} {}", title_str, b, d).unwrap();
            }
        }
    }
}

fn get_chunks() -> Vec<(u64, u64)> {
    let f = File::open(INDEX_FILE).expect("index file missing");
    let mut lines = BufReader::new(f).lines();

    let mut chunks = Vec::new();
    let mut prev = match lines.next() {
        Some(Ok(l)) => l,
        _ => return chunks,
    };

    for line in lines.flatten() {
        let a: u64 = prev.split(':').next().unwrap().parse().unwrap();
        let b: u64 = line.split(':').next().unwrap().parse().unwrap();
        if a != b {
            chunks.push((a, b - a));
        }
        prev = line;
    }

    chunks
}

fn main() {
    let chunks = get_chunks();
    println!("Loaded {} chunks", chunks.len());

    let output = File::create(OUTPUT_FILE).expect("cannot create output file");
    let writer = Mutex::new(BufWriter::new(output));

    chunks.par_iter().for_each(|chunk| {
        process_chunk(*chunk, &writer);
    });
}
