import os

path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\vk_cover_service.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("VkActivity.points_added", "VkActivity.points")
text = text.replace("async with httpx.AsyncClient() as client:", "async with httpx.AsyncClient(timeout=30.0) as client:")
text = text.replace('city_weather: str = "Москва"', 'city_weather: str = "Тюмень"')

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_cover_service.py successfully patched")
