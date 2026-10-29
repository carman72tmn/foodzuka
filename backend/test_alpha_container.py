from PIL import Image, ImageDraw, ImageFont

bg = Image.new("RGBA", (800, 300), (80, 40, 120, 255))

# 1. Overlay for alpha composite
overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

# Glass container box
box = (50, 50, 400, 150)
fill_color = (15, 15, 28, 185)       # 70% dark alpha
border_color = (255, 255, 255, 120)  # 50% white border
draw.rounded_rectangle(box, radius=16, fill=fill_color, outline=border_color, width=2)

# Alpha composite overlay over bg
bg = Image.alpha_composite(bg, overlay)

# Draw text on composite image
draw_bg = ImageDraw.Draw(bg)
try:
    font = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 26)
except:
    font = ImageFont.load_default()

draw_bg.text((70, 80), "Тест прозрачной подложки", fill=(255, 255, 255, 255), font=font)
bg.save("/tmp/test_container.png")
print("Alpha compositing test finished successfully!")
