import re
from PIL import Image, ImageDraw, ImageFont

def sanitize_text_for_font(text: str, font: ImageFont.FreeTypeFont) -> str:
    """Очищает или заменяет эмодзи, которые не поддерживаются шрифтом, чтобы не выводились ????"""
    # Карта замен популярного эмодзи на стильные текстовые иконки
    replacements = {
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
    for emoji, rep in replacements.items():
        text = text.replace(emoji, rep)
    
    # Фильтруем символы, у которых у шрифта маска пустая или '?'
    cleaned = []
    for char in text:
        # Проверяем, есть ли символ в TrueType
        mask = font.getmask(char)
        if mask.getbbox() is not None:
            cleaned.append(char)
        else:
            # Пропускаем или заменяем пробелом
            pass
    return "".join(cleaned)

font = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 24)
test_str = "👑 Лидер недели: Иван Иванов (45 б.) ⏰ 15:45"
sanitized = sanitize_text_for_font(test_str, font)
print("Original:", test_str)
print("Sanitized:", sanitized)
