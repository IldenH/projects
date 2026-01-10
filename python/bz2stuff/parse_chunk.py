import re
import bz2
import sys
from concurrent.futures import ProcessPoolExecutor

WIKI_FILE = "/BIG/wikipedia/wiki.xml.bz2"
INDEX_FILE = "short_index.txt"

wikitext = re.compile(b"<text.*?>(.*?)</text>", flags=re.DOTALL)


def get_articles(xml_f: str, chunk: tuple[int, int]) -> list[str]:
    offset, chunk_size = chunk
    bz = bz2.BZ2Decompressor()

    with open(xml_f, "rb") as f:
        f.seek(offset)
        comp_data = f.read(chunk_size)
        data = bz.decompress(comp_data)

    return re.findall(wikitext, data)


def get_chunks(index_f: str) -> list[tuple[int, int]]:
    chunks = []
    with open(index_f, "r") as f:
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


def process_chunk(c: tuple[int, int]) -> list[str]:
    return get_articles(WIKI_FILE, c)


def main():
    chunks = get_chunks(INDEX_FILE)
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(process_chunk, chunks))
    articles = [a for r in results for a in r]
    print(len(articles))


if __name__ == "__main__" and not sys.flags.interactive:
    main()
