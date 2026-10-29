import os
import httpx
from PIL import Image, ImageDraw, ImageFont

# Download Symbola font (supports all Unicode emojis as vector glyphs)
url = "https://github.com/nmoinvaz/fonts/raw/master/Symbola.ttf"
symbola_path = "/app/media/fonts/Symbola.ttf"

if not os.path.exists(symbola_path):
    print("Downloading Symbola.ttf...")
    resp = httpx.get(url, follow_redirects=True, timeout=30.0)
    if resp.status_code == 200:
        with open(symbola_path, "wb") as f:
            f.write(resp.content)
        print("Downloaded Symbola.ttf! Size:", os.path.getsize(symbola_path))

try:
    font_main = ImageFont.truetype("/app/media/fonts/Roboto-Bold.ttf", 24)
    font_emoji = ImageFont.truetype(symbola_path, 24)
    
    print("Symbola test 👑:", font_emoji.getbbox("👑"))
    print("Symbola test 🚀:", font_emoji.getbbox("🚀"))
    print("Symbola test 🍕:", font_emoji.getbbox("🍕"))
    print("Symbola test ⏰:", font_emoji.getbbox("⏰"))
except Exception as e:
    print("Error:", e)
