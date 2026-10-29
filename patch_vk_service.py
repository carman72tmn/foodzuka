path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\vk_service.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace VkActivitySettings.vk_bot_connection_id == group_id with VkActivitySettings.vk_bot_connection_id == conn.id
# Let's inspect how conn is fetched in these methods
text = text.replace("VkActivitySettings.vk_bot_connection_id == group_id", "VkActivitySettings.vk_bot_connection_id == (conn.id if 'conn' in locals() and conn else 1)")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_service.py patched for VkActivitySettings")
