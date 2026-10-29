from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_cover_bot import VkCoverBot

with Session(engine) as s:
    b = s.exec(select(VkCoverBot)).first()
    if b:
        print(f"ID: {b.id}, Active: {b.is_active}")
        print(f"Background: {b.background_image_url}")
        print(f"Update Interval: {b.update_interval}")
        print(f"Last Published: {b.last_published_at}")
        print(f"Widgets ({len(b.widgets)}): {b.widgets}")
    else:
        print("No bot found!")
