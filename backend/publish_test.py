import asyncio
from app.services.vk_cover_service import vk_cover_service
from app.models.vk_cover_bot import VkCoverBot
from app.core.database import engine
from sqlmodel import Session, select

async def publish_test():
    with Session(engine) as session:
        bot = session.exec(select(VkCoverBot).where(VkCoverBot.is_active == True)).first()
        if bot:
            print(f"Publishing cover bot ID {bot.id} ({bot.name}) to VK...")
            success = await vk_cover_service.publish_cover(session, bot)
            print(f"Publish result: {success}")
        else:
            print("No active cover bot found in DB!")

asyncio.run(publish_test())
