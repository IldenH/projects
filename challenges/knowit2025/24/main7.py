from PIL import Image, ImageDraw

# Open the original image
img = Image.open("juletreet.png")
ps = img.load()

# Coordinates to copy
pixels = [
    (562,292),
    (415,318),
    (395,339),
    (215,458),
    (283,553),
    (675,478),
    # (943,500),
    (486,586),
    (69,906),
    (821,717),
    (274,900),
    (701,723),
    (671,812)
]

# Create a blank image
img2 = Image.new("RGB", img.size, color=(0,0,0))
draw = ImageDraw.Draw(img2)

# Size of the rectangle
rect_size = 10
offset = rect_size // 2

# Sort pixels bottom-to-top, left-to-right
pixels_sorted = sorted(pixels, key=lambda p: (-p[1], p[0]))

# Draw rectangles
for x, y in pixels_sorted:
    color = ps[x, y]
    # Draw a rectangle centered at the pixel
    draw.rectangle(
        [x - offset, y - offset, x + offset, y + offset],
        fill=color
    )
    print((x, y), color)

img2.show()
