from PIL import Image

img = Image.open("juletreet.png")

pixels = [
    (562,292), # kanskje
    (415,318),
    (395,339), # kanskje
    (215,458), # kanskje
    (283,553),
    (675,478), # *
    (943,500),
    (486,586), # *
    (69,906),
    (821,717), # *
    (274,900), # kanskje
    (701,723), # *
    (671,812) # kanskje
]

ps = img.load()
assert ps is not None

found = {}

for y in reversed(range(img.height)):
    for x in range(img.width):
        if (x, y) in pixels:
            found[(x, y)] = ps[x, y]

for coord in pixels:
    if coord in found:
        print(coord, found[coord])


alphabet = "abcdefghijklmnopqrstuvwxyzæøå"
