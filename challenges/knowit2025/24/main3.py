
from PIL import Image

img = Image.open("juletreet.png")
ps = img.load()

# 8 unique red pixels
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

alphabet = "abcdefghijklmnopqrstuvwxyzæøå"

# Sort red pixels by Y (top->bottom) or X (left->right)
red_sorted = sorted(red_pixels, key=lambda p: p[1])  # try vertical order

# Step 1: compute bits from R-B
threshold = 100  # you can tweak if needed
bits = []
for _, _, (r, g, b, _) in red_sorted:
    bit = 1 if (r - b) > threshold else 0
    bits.append(bit)

print("Bits:", bits)

# Step 2: convert 8 bits into a byte
byte_value = 0
for i, b in enumerate(bits):
    byte_value |= b << (7 - i)  # MSB first

print("Byte value:", byte_value)
print("ASCII char:", chr(byte_value))

# Step 3 (optional): split each 4-bit nibble to map to alphabet (0-15)
nibbles = [(byte_value >> 4) & 0xF, byte_value & 0xF]
letters = "".join(alphabet[n % len(alphabet)] for n in nibbles)
print("Two-letter mapping:", letters)
