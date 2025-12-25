# Juletree pixel decoding

alphabet = "abcdefghijklmnopqrstuvwxyzæøå"

# 8 unike røde pixler: (x, y, (R, G, B, A))
red_pixels = [
    (562, 292, (236, 125, 111, 255)),
    (395, 339, (154, 110, 95, 255)),
    (215, 458, (236, 128, 116, 255)),
    (675, 478, (236, 127, 114, 255)),
    (486, 586, (166, 109, 94, 255)),
    (69, 906, (236, 133, 121, 255)),
    (274, 900, (176, 107, 91, 255)),
    (671, 812, (236, 129, 117, 255))
]

# Sorter pikslene venstre -> høyre
red_pixels_sorted = sorted(red_pixels, key=lambda p: p[0])

# Dekod til bokstaver
decoded = []
for x, y, (r, g, b, a) in red_pixels_sorted:
    index = (r - b) % len(alphabet)
    letter = alphabet[index]
    decoded.append(letter)

# Vis resultat
print("Dekodet tekst (8 første bokstaver):", "".join(decoded))
