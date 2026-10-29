from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 24)

text_with_emoji = "👑 Лидер недели: Иван Иванов (45 б.) ⏰ 15:45"
img = Image.new("RGBA", (600, 100), (20, 20, 30, 255))
draw = ImageDraw.Draw(img)

draw.text((10, 10), text_with_emoji, fill=(255, 255, 255, 255), font=font)
img.save("/tmp/test_emoji.png")

# Read bbox / check
print("Rendered successfully without exception")
