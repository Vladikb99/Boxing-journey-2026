from pathlib import Path

from PIL import Image, ImageFilter


project_root = Path(__file__).resolve().parent

png_path = project_root / "assets" / "logos" / "boxing_logo_premium.png"
output_png_path = project_root / "assets" / "logos" / "boxing_logo_shortcut.png"
output_ico_path = project_root / "assets" / "logos" / "boxing_logo_shortcut.ico"

if not png_path.exists():
    raise FileNotFoundError(f"Could not find logo PNG: {png_path}")

img = Image.open(png_path).convert("RGBA")

# ============================================================
# Crop away both transparent and near-black empty space
# ============================================================

bbox = img.getbbox()

if bbox:
    img = img.crop(bbox)

# Build a mask of pixels that are NOT almost black and not transparent
alpha = img.getchannel("A")
rgb = img.convert("RGB")

mask = Image.new("L", img.size, 0)
pixels_rgb = rgb.load()
pixels_a = alpha.load()
pixels_m = mask.load()

for y in range(img.height):
    for x in range(img.width):
        r, g, b = pixels_rgb[x, y]
        a = pixels_a[x, y]

        # Keep bright glove pixels, remove dark background pixels
        if a > 10 and (r > 35 or g > 35 or b > 35):
            pixels_m[x, y] = 255

bbox2 = mask.getbbox()
if bbox2:
    img = img.crop(bbox2)

# ============================================================
# Make final icon with black background and large glove
# ============================================================

canvas_size = 512
canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 255))

target_size = 470
img.thumbnail((target_size, target_size), Image.LANCZOS)

x = (canvas_size - img.width) // 2
y = (canvas_size - img.height) // 2

# Soft gold glow
glow = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
glow_layer = Image.new("RGBA", img.size, (255, 220, 40, 140))
glow_layer.putalpha(img.getchannel("A"))

glow.paste(glow_layer, (x, y), glow_layer)
glow = glow.filter(ImageFilter.GaussianBlur(12))

canvas.alpha_composite(glow)
canvas.paste(img, (x, y), img)

canvas.save(output_png_path)

canvas.save(
    output_ico_path,
    format="ICO",
    sizes=[
        (16, 16),
        (24, 24),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (256, 256),
    ],
)

print(f"Created PNG: {output_png_path}")
print(f"Created ICO: {output_ico_path}")