path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\api\vk.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("db: AsyncSession = Depends(get_db)", "db: AsyncSession = Depends(get_async_session)")
text = text.replace("from app.db.session import get_session", "from app.db.session import get_session, get_async_session")

# If get_async_session not imported, let's ensure it is imported
if "get_async_session" not in text:
    text = "from app.core.database import get_async_session\n" + text

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk.py session dependency fixed")
