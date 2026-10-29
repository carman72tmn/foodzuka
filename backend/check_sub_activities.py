import json
from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_cover_bot import VkCoverSubscriberActivity

with Session(engine) as db:
    acts = db.exec(select(VkCoverSubscriberActivity)).all()
    print(f"FOUND {len(acts)} SUBSCRIBER ACTIVITIES:")
    for a in acts:
        print(f"ID: {a.id}, User ID: {a.vk_user_id}, Name: '{a.first_name} {a.last_name}', Score: {a.score}, Avatar: {a.avatar_url}")
