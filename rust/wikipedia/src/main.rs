use bzip2::read::MultiBzDecoder;
use std::error::Error;
use std::fs::File;
use std::io::Read;

fn main() -> Result<(), Box<dyn Error>> {
    let f = File::open("abc.txt.bz2")?;
    let mut decompressor = MultiBzDecoder::new(f);
    // let mut buffer = Vec::new();
    let mut buffer = String::new();
    decompressor.read_to_string(&mut buffer)?;
    Ok(())
}
