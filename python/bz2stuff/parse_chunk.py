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
    def process(line: str, line_next: str):
        b = lambda l: int(l.split(":")[0])
        byte = b(line_next)
        start_byte = b(line)
        data_length = byte - start_byte
        return start_byte, data_length


    chunks = []

    with open(index_f, "r") as f:
        prev_line = f.readline()
        for _, line in enumerate(f, start=1):
            if prev_line.split(":")[0] != line.split(":")[0]:
                chunks.append(process(prev_line, line))
            prev_line = line
    return chunks

def process_chunk(c):
    return get_articles(WIKI_FILE, c)

if __name__ == "__main__" and not sys.flags.interactive:
    chunks = get_chunks(INDEX_FILE)
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(process_chunk, chunks))
    articles = [a for r in results for a in r]
    print(len(articles))
