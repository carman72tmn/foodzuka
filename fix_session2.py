path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\api\vk.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace get_async_session with get_session
text = text.replace("db: AsyncSession = Depends(get_async_session)", "db: Session = Depends(get_session)")
text = text.replace("from app.core.database import get_async_session\n", "")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk.py session fixed to get_session")
