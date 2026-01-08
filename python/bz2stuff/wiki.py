import xml.etree.ElementTree as ET
import bz2

# https://stackoverflow.com/questions/60101844/how-do-i-use-python-to-parse-large-wikipedia-dump-in-xml-bz2-format-using-multi
def get_wikitext(dump_filename: str, offset, page_id=None, title=None, namespace_id=None, verbose=True, block_size=256*1024):
    unzipper = bz2.BZ2Decompressor()

    uncompressed_data = b""
    with open(dump_filename, "rb") as infile:
        infile.seek(int(offset))

        while True:
            compressed_data = infile.read(block_size)
            try:
                uncompressed_data += unzipper.decompress(compressed_data)
            except EOFError:
                break
            if compressed_data == '':
                if unzipper.needs_input:
                    break
                raise Exception("Failed to read a complete stream")


    uncompressed_text = uncompressed_data.decode("utf-8")
    xml_data = "<root>" + uncompressed_text + "</root>"
    root = ET.fromstring(xml_data)
    for page in root.findall("page"):
        if title is not None:
            if title != page.find("title").text:
                continue
        if namespace_id is not None:
            if namespace_id != int(page.find("ns").text):
                continue
        if page_id is not None:
            if page_id != int(page.find("id").text):
                continue
        revision = page.find("revision")
        assert revision is not None
        wikitext = revision.find("text")
        assert wikitext is not None
        return wikitext.text

    return None


def example_usage():
    index_line = "600:12:Anarchism"
    offset, page_id, title = index_line.split(":")
    dump_file = "enwiki-dump/enwiki-20231101-pages-articles-multistream.xml.bz2"

    wikitext = get_wikitext(dump_file, int(offset), page_id=int(page_id))
    print(wikitext)
