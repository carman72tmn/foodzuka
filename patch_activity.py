path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\vk_activity_service.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Fix item_id format mismatch in duplicate check
text = text.replace('VkActivity.item_id == f"comment_{comment_id}"', 'VkActivity.item_id == f"comment_{post_id}_{comment_id}"')

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_activity_service.py patched")
