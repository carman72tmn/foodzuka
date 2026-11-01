import asyncio
import json
from sqlmodel import Session
from app.core.database import engine
from app.models.chat import MultichatAccount
from app.services.max_bridge_service import MAX_SESSIONS_DIR
import pymax

async def run():
    with Session(engine) as db:
        acc = db.get(MultichatAccount, 9)
        meta = json.loads(acc.session_string or "{}")
        db_name = meta.get("db_name")
        client = pymax.WebClient(session_name=db_name, work_dir=MAX_SESSIONS_DIR)
        await client._app.start()
        chats = await client.fetch_chats()
        for ch in chats:
            if ch.id < 0:
                print("GROUP:", ch.id, ch.title, "photo_id:", getattr(ch, "photo_id", None), "base_url:", getattr(ch, "base_url", None), "icon:", getattr(ch, "icon", None))
        await client.close()

if __name__ == "__main__":
    asyncio.run(run())
