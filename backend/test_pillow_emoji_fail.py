from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 24)

# Test strings with various emojis
test_cases = [
    "👑 Лидер недели: Иван",
    "🚀 Акция дня: Скидка 20%",
    "💥 Промокод: VK2026",
    "★ Лидер недели: Иван"
]

for tc in test_cases:
    img = Image.new("RGBA", (500, 50), (20, 20, 30, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), tc, fill=(255, 255, 255), font=font)
    print(f"BBOX for '{tc}': {draw.textbbox((0, 0), tc, font=font)}")
