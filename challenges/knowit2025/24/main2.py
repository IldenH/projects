from PIL import Image
from math import floor

img = Image.open("juletreet.png")
ps = img.load()

alphabet = "abcdefghijklmnopqrstuvwxyzæøå"
N = len(alphabet)

pixels = [
    (562,292),
    (415,318),
    (395,339),
    (215,458),
    (283,553),
    (675,478),
    (943,500),   # out of bounds
    (486,586),
    (69,906),
    (821,717),
    (274,900),
    (701,723),
    (671,812)
]

# --------------------------------------------------
# 1. Read pixels (ignore out-of-bounds)
# --------------------------------------------------
pixel_data = {}
for x, y in pixels:
    if 0 <= x < img.width and 0 <= y < img.height:
        pixel_data[(x, y)] = ps[x, y]

print("All valid pixels:")
for k, v in pixel_data.items():
    print(k, v)

# --------------------------------------------------
# 2. Classify colors
# --------------------------------------------------
def classify(r, g, b):
    if r > 100 and g < 150 and b < 150:
        return "red"
    if g > 80 and b > 80 and r < 100:
        return "aqua"
    if r > 240 and g > 240 and b > 240:
        return "white"
    return "other"

classified = {}
for (x, y), (r, g, b, a) in pixel_data.items():
    classified[(x, y)] = classify(r, g, b)

print("\nClassified:")
for k, v in classified.items():
    print(k, v)

# --------------------------------------------------
# 3. Extract UNIQUE red pixels
# --------------------------------------------------
red_pixels = []
seen = set()

for (x, y), color in classified.items():
    if color == "red":
        if (x, y) not in seen:
            seen.add((x, y))
            red_pixels.append((x, y, pixel_data[(x, y)]))

print("\nUnique RED pixels:", len(red_pixels))
for p in red_pixels:
    print(p)

# --------------------------------------------------
# 4. Sort red pixels (top → bottom)
# --------------------------------------------------
red_sorted_y = sorted(red_pixels, key=lambda p: p[1])
red_sorted_x = sorted(red_pixels, key=lambda p: p[0])

# --------------------------------------------------
# 5. Helper for alphabet mapping
# --------------------------------------------------
def to_letter(n):
    return alphabet[n % N]

# --------------------------------------------------
# 6. Decode methods
# --------------------------------------------------
print("\n=== METHOD A: ORDER ONLY (A, B, C...) ===")
print("Y-order:", "".join(alphabet[i] for i in range(len(red_sorted_y))))
print("X-order:", "".join(alphabet[i] for i in range(len(red_sorted_x))))

print("\n=== METHOD B: RGB BASED ===")
for name, pixels in [("Y-order", red_sorted_y), ("X-order", red_sorted_x)]:
    print(f"\n{name}")
    s1 = ""  # red channel
    s2 = ""  # green channel
    s3 = ""  # red-blue
    for _, _, (r, g, b, _) in pixels:
        s1 += to_letter(r)
        s2 += to_letter(g)
        s3 += to_letter(abs(r - b))
    print("R   :", s1)
    print("G   :", s2)
    print("R-B :", s3)

print("\n=== METHOD C: COORDINATES ===")
for name, pixels in [("Y-order", red_sorted_y), ("X-order", red_sorted_x)]:
    print(f"\n{name}")
    sx = ""
    sy = ""
    sxy = ""
    for x, y, _ in pixels:
        sx += to_letter(x)
        sy += to_letter(y)
        sxy += to_letter(x + y)
    print("x   :", sx)
    print("y   :", sy)
    print("x+y :", sxy)

print("\n=== METHOD D: AVERAGES ===")
for name, pixels in [("Y-order", red_sorted_y), ("X-order", red_sorted_x)]:
    print(f"\n{name}")
    s = ""
    for _, _, (r, g, b, _) in pixels:
        avg = floor((r + g + b) / 3)
        s += to_letter(avg)
    print("avg :", s)
