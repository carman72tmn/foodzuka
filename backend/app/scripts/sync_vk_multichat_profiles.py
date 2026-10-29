import sys
import os
import httpx

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import Session, select, update
from app.core.database import engine
from app.models.chat import MultichatMessage
from app.models.vk_user import VkUser
from app.models.vk_settings import VkSettings
from app.models.vk_bot_connection import VkBotConnection

def sync_profiles():
    print("Starting VK multichat profiles enrichment...")
    with Session(engine) as db:
        # Получаем рабочий токен VK
        bot_conn = db.exec(select(VkBotConnection).where(VkBotConnection.is_active == True)).first()
        token = bot_conn.vk_bot_token if bot_conn else None
        if not token:
            vk_settings = db.exec(select(VkSettings)).first()
            token = vk_settings.vk_bot_token if vk_settings else None
            
        if not token:
            print("No active VK bot token found!")
            return

        # Находим всех уникальных VK пользователей в сообщениях
        raw_vk_ids = db.exec(
            select(MultichatMessage.peer_id)
            .where(MultichatMessage.channel == "vk")
            .group_by(MultichatMessage.peer_id)
        ).all()

        vk_ids = [int(p) for p in raw_vk_ids if p and p.isdigit()]
        print(f"Found {len(vk_ids)} unique VK users to inspect.")

        if not vk_ids:
            return

        # Запрашиваем пачками до 500 пользователей за один вызов VK API
        chunk_size = 500
        for i in range(0, len(vk_ids), chunk_size):
            chunk = vk_ids[i:i + chunk_size]
            user_ids_str = ",".join(str(uid) for uid in chunk)
            
            try:
                resp = httpx.get(
                    "https://api.vk.ru/method/users.get",
                    params={
                        "user_ids": user_ids_str,
                        "fields": "photo_50,domain",
                        "access_token": token,
                        "v": "5.131"
                    },
                    timeout=15.0
                )
                data = resp.json()
                if "response" in data:
                    profiles = data["response"]
                    print(f"Received {len(profiles)} profiles from VK API.")
                    for p in profiles:
                        uid = p.get("id")
                        fn = p.get("first_name", "")
                        ln = p.get("last_name", "")
                        full_name = f"{fn} {ln}".strip()
                        photo = p.get("photo_50")
                        domain = p.get("domain")

                        if not uid or not full_name:
                            continue

                        # 1. Обновляем / создаем запись в VkUser
                        vk_user = db.exec(select(VkUser).where(VkUser.vk_id == uid)).first()
                        if vk_user:
                            vk_user.first_name = fn
                            vk_user.last_name = ln
                            vk_user.photo_50 = photo
                            if domain:
                                vk_user.screen_name = domain
                            db.add(vk_user)
                        else:
                            new_u = VkUser(
                                vk_id=uid,
                                first_name=fn,
                                last_name=ln,
                                photo_50=photo,
                                screen_name=domain
                            )
                            db.add(new_u)

                        # 2. Обновляем peer_name и peer_avatar в MultichatMessage
                        db.execute(
                            update(MultichatMessage)
                            .where(MultichatMessage.channel == "vk", MultichatMessage.peer_id == str(uid))
                            .values(peer_name=full_name, peer_avatar=photo)
                        )
                    
                    db.commit()
                    print(f"Processed chunk {i // chunk_size + 1}")
                else:
                    print("VK API Error:", data.get("error"))
            except Exception as e:
                print(f"Error fetching chunk {i}: {e}")

        print("VK profiles enrichment completed successfully!")

if __name__ == "__main__":
    sync_profiles()
