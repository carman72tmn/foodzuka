import os
from PIL import Image, ImageDraw, ImageFont

font_path = "/app/media/fonts/Roboto-Bold.ttf"
print("File exists:", os.path.exists(font_path))
if os.path.exists(font_path):
    print("Size:", os.path.getsize(font_path))

try:
    font = ImageFont.truetype(font_path, 24)
    print("Font loaded successfully!")
except Exception as e:
    print("Font load failed:", e)
    font = ImageFont.load_default()

img = Image.new("RGBA", (500, 100), (20, 20, 30, 255))
draw = ImageDraw.Draw(img)
draw.text((10, 10), "Лидер недели: Иван Иванов 👑", fill=(255, 255, 255, 255), font=font)
img.save("/tmp/test_font.png")
print("Saved /tmp/test_font.png")
