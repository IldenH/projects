import re
import bz2
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import ByteString

WIKI_FILE = "/BIG/wikipedia/wiki.xml.bz2"
INDEX_FILE = "short_index.txt"

PAGE_RE = re.compile(b"<page.*?>(.*?)</page>", flags=re.DOTALL)
TITLE_RE = re.compile(b"<title.*?>(.*?)</title>", flags=re.DOTALL)
INFO_RE = re.compile(b"{{Infobox(.*?)}}", flags=re.DOTALL)

YEAR_REGEX = re.compile(rb"\b([0-9]{3,4})\b", re.ASCII)
YEAR = datetime.now().year

BIRTH_RE = re.compile(rb"\|.*?birth_date.*?=(.*)", re.ASCII)
DEATH_RE = re.compile(rb"\|.*?death_date.*?=(.*)", re.ASCII)


def parse_year(s: ByteString) -> int | None:
    m = re.search(YEAR_REGEX, s)
    if not m:
        return None
    year = int(m.group(1))
    return year if year <= YEAR else None


def process_chunk(chunk: tuple[int, int]) -> None:
    offset, chunk_size = chunk
    bz = bz2.BZ2Decompressor()

    with open(WIKI_FILE, "rb") as f:
        f.seek(offset)
        comp_data = f.read(chunk_size)
        data = bz.decompress(comp_data)

    pages = re.findall(PAGE_RE, data)
    txts = [
        (title.group(1), txt.group(1))
        for p in pages
        if (txt := re.search(INFO_RE, p)) and (title := re.search(TITLE_RE, p))
    ]
    with open("people.txt", "a") as f:
        for title, txt in txts:
            birth_m = re.search(BIRTH_RE, txt)
            if not birth_m:
                continue
            birth = birth_m.group(1)
            death_m = re.search(DEATH_RE, txt)
            if not death_m:
                continue
            death = death_m.group(1)
            birth_year = parse_year(birth)
            death_year = parse_year(death)
            f.write(
                f"{title.decode('utf-8')} {birth_year} {death_year}\n"
            )


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
