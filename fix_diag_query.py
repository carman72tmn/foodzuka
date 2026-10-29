path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\api\vk.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace async call on synchronous session
target = """    stmt = select(VkBotConnection).where(VkBotConnection.id == connection_id)
    res = await db.exec(stmt)
    conn = res.first()"""

replacement = """    stmt = select(VkBotConnection).where(VkBotConnection.id == connection_id)
    conn = db.exec(stmt).first()"""

text = text.replace(target, replacement)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk.py diagnostics sync query fixed")
