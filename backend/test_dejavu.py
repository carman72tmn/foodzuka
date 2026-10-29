import os
import httpx
from PIL import Image, ImageDraw, ImageFont

url = "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans.ttf"
path = "/app/media/fonts/DejaVuSans.ttf"

if not os.path.exists(path):
    print("Downloading DejaVuSans.ttf...")
    resp = httpx.get(url, follow_redirects=True, timeout=30.0)
    if resp.status_code == 200:
        with open(path, "wb") as f:
            f.write(resp.content)
        print("Downloaded DejaVuSans.ttf successfully! Size:", os.path.getsize(path))

try:
    font = ImageFont.truetype(path, 24)
    print("DejaVuSans bbox for ⏰:", font.getbbox("⏰"))
    print("DejaVuSans bbox for 👑:", font.getbbox("👑"))
except Exception as e:
    print("Error:", e)
