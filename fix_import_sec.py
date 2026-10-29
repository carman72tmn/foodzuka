path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\api\vk_marketing_endpoints.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("from app.core.security import get_current_user", "# no get_current_user")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_marketing_endpoints.py import fixed")
