import asyncio
import json
from sqlmodel import Session, select
from app.core.database import engine
from app.models.chat import MultichatAccount
from app.services.max_bridge_service import MAX_SESSIONS_DIR
import pymax

async def inspect_chats_and_users():
    with Session(engine) as db:
        acc = db.get(MultichatAccount, 9)
        meta = json.loads(acc.session_string or "{}")
        db_name = meta.get("db_name") or acc.token
        
        client = pymax.WebClient(session_name=db_name, work_dir=MAX_SESSIONS_DIR)
        await client._app.start()
        chats = await client.fetch_chats()
        print(f"Total fetched chats: {len(chats)}")
        
        # Collect user ids from chats
        user_ids = []
        for ch in chats[:15]:
            print("\n--- CHAT ---")
            print("ID:", getattr(ch, "id", None))
            print("Title:", getattr(ch, "title", None))
            print("Chat dict/fields:", {k: getattr(ch, k, None) for k in dir(ch) if not k.startswith('_')})
            if hasattr(ch, "users"):
                print("Users:", ch.users)
            
            chat_id = getattr(ch, "id", None)
            if chat_id and chat_id > 0: # 1-on-1 user chat
                user_ids.append(chat_id)
                
        if user_ids:
            print(f"\nFetching users for IDs: {user_ids[:5]}")
            users = await client.fetch_users(user_ids[:5])
            print(f"Fetched {len(users)} users:")
            for u in users:
                print("USER:", u.id, "phone:", getattr(u, "phone", None), "names:", getattr(u, "names", None), "avatar:", getattr(u, "base_url", None), getattr(u, "photo_id", None))
                print("All user fields:", {k: getattr(u, k, None) for k in dir(u) if not k.startswith('_')})
                
        await client.close()

if __name__ == "__main__":
    asyncio.run(inspect_chats_and_users())
