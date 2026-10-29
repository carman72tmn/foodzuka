path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\vk_first_comment_service.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("re.sub(r'\\s+', ' ', cleaned_comment).strip()", "re.sub(r'[ \\t]+', ' ', cleaned_comment).strip()")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_first_comment_service.py patched")
