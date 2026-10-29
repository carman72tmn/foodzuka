from PIL import ImageFont

font = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 24)

emojis = ["👑", "⏰", "🌤", "🚚", "🎉", "🎁", "🍕", "⭐️"]
for e in emojis:
    bbox = font.getbbox(e)
    # Check if glyph exists
    has_glyph = font.getmask(e).getbbox() is not None
    print(f"Emoji '{e}' bbox: {bbox}, has_mask: {has_glyph}")
