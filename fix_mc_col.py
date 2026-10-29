path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\vk_token_manager.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace MultichatAccount.is_active == True with MultichatAccount.status == 'active'
text = text.replace("MultichatAccount.is_active == True", "MultichatAccount.status == 'active'")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_token_manager.py multichat column status fixed")
