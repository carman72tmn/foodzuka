from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGBA', (200, 200), (50, 50, 50, 255))
draw = ImageDraw.Draw(img)

# Test rounded rectangle
draw.rounded_rectangle((20, 20, 180, 180), radius=15, fill=(20, 20, 40, 200), outline=(255, 215, 0, 255), width=2)

# Test text with stroke
try:
    font = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 28)
except:
    font = ImageFont.load_default()

draw.text((40, 40), "Тест PIL", fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0), font=font)
print("PIL rounded_rectangle & text stroke fully supported!")
