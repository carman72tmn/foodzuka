from app.core.database import engine
from sqlmodel import Session, select
from app.models.vk_user import VkUser

with Session(engine) as session:
    u = session.get(VkUser, 40957506)
    if u:
        print(f"ID: {u.vk_id}")
        print(f"Name: {u.first_name} {u.last_name}")
        print(f"Phone: {u.phone}")
        print(f"is_linked: {u.is_linked}")
        print(f"notifications_enabled: {u.notifications_enabled}")
        print(f"is_blocked: {u.is_blocked}")
    else:
        print("Not found")
