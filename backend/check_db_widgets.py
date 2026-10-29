import json
from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_cover_bot import VkCoverBot

with Session(engine) as db:
    bot = db.exec(select(VkCoverBot)).first()
    if bot:
        print("WIDGETS IN DB:")
        print(json.dumps(bot.widgets, ensure_ascii=False, indent=2))
    else:
        print("NO BOT IN DB")
