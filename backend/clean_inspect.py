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
        db_name = meta.get("db_name") or acc.token
        
        client = pymax.WebClient(session_name=db_name, work_dir=MAX_SESSIONS_DIR)
        await client._app.start()
        chats = await client.fetch_chats()
        
        user_ids = [ch.id for ch in chats if getattr(ch, "id", 0) > 0][:10]
        users = await client.fetch_users(user_ids) if user_ids else []
        user_map = {u.id: u for u in users}
        
        for ch in chats[:10]:
            cid = ch.id
            title = ch.title
            u = user_map.get(cid)
            phone = getattr(u, "phone", None) if u else None
            names = getattr(u, "names", None) if u else None
            photo_id = getattr(u, "photo_id", None) if u else getattr(ch, "photo_id", None)
            base_url = getattr(u, "base_url", None) if u else getattr(ch, "base_url", None)
            base_raw = getattr(u, "base_raw_url", None) if u else getattr(ch, "base_raw_url", None)
            print(f"CHAT {cid}: title='{title}', user_phone='{phone}', names={names}, photo_id='{photo_id}', base_url='{base_url}', base_raw='{base_raw}'")
            
        await client.close()

if __name__ == "__main__":
    asyncio.run(run())
