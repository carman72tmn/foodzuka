from PIL import Image, ImageDraw, ImageFont

def sanitize_text_strict(text: str) -> str:
    """Полностью и строго очищает текст от несовместимых эмодзи и юникод-символов, гарантируя отстутствие ???? в FreeType"""
    # Сопоставление всевозможных эмодзи на стильные векторные иконки
    emoji_map = {
        "👑": "★", "👑": "★", "⏰": "•", "🌤": "☀", "⏱": "•", "🚚": "▶", 
        "🎉": "✦", "🎁": "★", "🍕": "●", "⭐️": "★", "🔥": "▲", "📝": "◆",
        "🏆": "★", "🥇": "★", "🥈": "★", "🥉": "★", "👤": "●", "💬": "◆",
        "❤️": "★", "👍": "★", "⚡️": "⚡", "⚡": "⚡", "🎁": "★", "🚀": "▲",
        "💥": "✦", "✨": "✦", "☀️": "☀", "📅": "•"
    }
    
    for emoji, rep in emoji_map.items():
        text = text.replace(emoji, rep)
        
    cleaned = []
    for char in text:
        code = ord(char)
        # Разрешаем латиницу (U+0000 - U+007F), доп. знаки (U+0080 - U+00FF), кириллицу (U+0400 - U+04FF)
        # и проверенные символы шрифта (★, •, ☀, ▶, ✦, ●, ▲, ◆, ⚡)
        if code <= 0x04FF or code in (0x2605, 0x2022, 0x2600, 0x25B6, 0x2721, 0x25CF, 0x25B2, 0x25C6, 0x26A1):
            cleaned.append(char)
        else:
            # Символы выходящие за пределы шрифта пропускаем, замещая на чистый символ или пробел
            cleaned.append(" ")

    # Убираем возможные двойные пробелы
    res = "".join(cleaned)
    while "  " in res:
        res = res.replace("  ", " ")
    return res

font = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 24)
test_inputs = [
    "👑 Лидер недели: Иван Иванов (45 б.) ⏰ 15:45",
    "🚀 Акция дня: Скидка 20% ⚡️",
    "🎉 Победитель: Анна С. (Роллы 🍕)",
    "🚚 Сегодня доставлено: 42 заказа 💥"
]

for inp in test_inputs:
    san = sanitize_text_strict(inp)
    img = Image.new("RGBA", (600, 50), (20, 20, 30, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), san, fill=(255, 255, 255), font=font)
    print(f"INPUT: '{inp}' => SANITIZED: '{san}'")
