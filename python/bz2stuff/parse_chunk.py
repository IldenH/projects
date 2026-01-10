import re
import bz2
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import ByteString

WIKI_FILE = "/BIG/wikipedia/wiki.xml.bz2"
INDEX_FILE = "short_index.txt"

wikitext = re.compile(b"<text.*?>(.*?)</text>", flags=re.DOTALL)


YEAR_REGEX = re.compile(rb"\b([0-9]{1,4})\b", re.ASCII)
DAYS_MONTH = 31
YEAR = datetime.now().year

NAME_RE = re.compile(rb"\|.*?name.*?=(.*)", re.ASCII)
BIRTH_RE = re.compile(rb"\|.*?birth_date.*?=(.*)", re.ASCII)
DEATH_RE = re.compile(rb"\|.*?death_date.*?=(.*)", re.ASCII)

def parse_year(s: ByteString) -> list[int]:
    return [
        year
        for m in re.findall(YEAR_REGEX, s) or []
        if (year := int(m)) > DAYS_MONTH and year <= YEAR
    ]

def process_chunk(chunk: tuple[int, int]) -> None:
    offset, chunk_size = chunk
    bz = bz2.BZ2Decompressor()

    with open(WIKI_FILE, "rb") as f:
        f.seek(offset)
        comp_data = f.read(chunk_size)
        data = bz.decompress(comp_data)

    txts = re.findall(wikitext, data)
    with open("abc.txt", "a") as f:
        for txt in txts:
            name_m = re.search(NAME_RE, txt)
            if not name_m:
                continue
            name = name_m.group(1)
            if not name:
                continue
            birth_m = re.search(BIRTH_RE, txt)
            if not birth_m:
                continue
            birth = birth_m.group(1)
            if not birth:
                continue
            death_m = re.search(DEATH_RE, txt)
            if not death_m:
                continue
            death = death_m.group(1)
            if death:
                f.write(f"{name.decode("utf-8")} {parse_year(birth)[0]} {parse_year(death)[0]}\n")


def get_chunks() -> list[tuple[int, int]]:
    chunks = []
    with open(INDEX_FILE, "r") as f:
        prev_line = f.readline()
        for line in f:
            start_byte = prev_line.split(":")[0]
            byte = line.split(":")[0]
            if start_byte != byte:
                start = int(start_byte)
                end = int(byte)
                chunks.append((start, end - start))
            prev_line = line
    return chunks



def main():
    chunks = get_chunks()
    with ProcessPoolExecutor() as executor:
        executor.map(process_chunk, chunks)


if __name__ == "__main__" and not sys.flags.interactive:
    main()
