from PIL import Image, ImageDraw, ImageFont

def render_smart_text(draw, pos, text, font, fill, stroke_width=0, stroke_fill=None):
    """Отрисовывает текст посимвольно/посегментно, надежно заменяя эмодзи на строгие векторные символы и избегая ????"""
    emoji_map = {
        "👑": "★",
        "⏰": "•",
        "🌤": "☀",
        "⏱": "⏱",
        "🚚": "▶",
        "🎉": "✦",
        "🎁": "🎁",
        "🍕": "●",
        "⭐️": "★",
        "🔥": "▲",
        "📝": "◆"
    }
    
    # 1. Заменяем известные цветные эмодзи на стильные графические иконки
    for emoji, symbol in emoji_map.items():
        text = text.replace(emoji, symbol)
        
    # 2. Формируем безопасный текст для TrueType
    safe_chars = []
    for char in text:
        code = ord(char)
        # Обычные символы (латиница, цифры, кириллица, знаки препинания, спец-символы)
        if code <= 0x04FF or code in (0x2605, 0x2022, 0x2600, 0x25B6, 0x2721, 0x25CF, 0x25B2, 0x25C6):
            safe_chars.append(char)
        else:
            # Ограничиваем несовместимые эмодзи
            pass
            
    safe_text = "".join(safe_chars)
    
    kwargs = {}
    if stroke_width > 0 and stroke_fill:
        kwargs = {"stroke_width": stroke_width, "stroke_fill": stroke_fill}
        
    draw.text(pos, safe_text, fill=fill, font=font, **kwargs)

img = Image.new("RGBA", (500, 80), (20, 20, 30, 255))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 24)

render_smart_text(draw, (10, 10), "👑 Лидер недели: Иван Иванов (45 б.) ⏰ 15:45", font, (255, 255, 255))
img.save("/tmp/test_smart_text.png")
print("Rendered smart text without any question marks!")
