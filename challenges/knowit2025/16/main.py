from PIL import Image, ImageColor
import re

img = Image.new("RGB", (1024, 1024), "white")
pixels = img.load()
assert pixels is not None

with open("input.txt") as f:
    contents = f.read().split()
    ps = [re.search(r"\[(.*),(.*)\]\((.*)\)", c).groups() for c in contents]

for p in ps:
    pixels[int(p[0]), int(p[1])] = ImageColor.getrgb(f"#{p[2]}")

img.show()
