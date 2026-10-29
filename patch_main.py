p = "/root/foodzuka/backend/main.py"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

if "vk_marketing_endpoints" not in text:
    target = 'app.include_router(vk.router, prefix="/api/v1/vk", tags=["VK"])'
    addition = 'from app.api import vk_marketing_endpoints\napp.include_router(vk_marketing_endpoints.router, prefix="/api/v1/vk", tags=["VK Marketing Bots"])'
    text = text.replace(target, target + "\n" + addition)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    print("main.py updated")
else:
    print("already in main.py")
