import bz2
import sys
import csv
import shutil

bz = bz2.BZ2Decompressor()

# bz.decompress()

# https://alchemy.pub/wikipedia
def search_index(term, f):
    byte_flag = False
    data_length = 0
    start_byte = 0
    f = open(f, 'r')
    for line in csv.reader(f, delimiter=':'):
        byte = int(line[0])
        if not byte_flag and term == line[2]:
            start_byte = byte
            byte_flag = True
        elif byte_flag and byte != start_byte:
            data_length = byte - start_byte
            break
    f.close()
    return start_byte, data_length

# https://alchemy.pub/wikipedia
def decompress_chunk(f, start_byte, data_length):
    temp_f = "chunk.bz2"
    decomp_f = "chunk.xml"
    with open(f, 'rb') as f:
        f.seek(start_byte)
        data = f.read(data_length)
    with open(temp_f, 'wb') as f:
        f.write(data)
    with bz2.BZ2File(temp_f) as f_src, open(decomp_f, 'wb') as f_dest:
        shutil.copyfileobj(f_src, f_dest)


if __name__ == "__main__" and not sys.flags.interactive:
    assert len(sys.argv) >= 2
    # with bz2.open(sys.argv[1]) as f:
    #     bz.decompress(f, max_length=1)


