import asyncio
from sqlmodel import Session, select
from app.core.database import engine
from app.services.vk_cover_service import vk_cover_service
from app.models.vk_cover_bot import VkCoverBot

async def test():
    with Session(engine) as db:
        bot = db.exec(select(VkCoverBot)).first()
        if bot:
            print("Publishing cover with period selection & strict emoji sanitizer...")
            bot.widgets = [
                { "type": "clock", "x": 260, "y": 120, "font_size": 28, "color": "#ffffff", "bg_style": "glass", "container_padding": 12, "container_radius": 14, "text_shadow": True, "text_stroke": True, "icon": "•", "show_date": True },
                { "type": "weather", "x": 880, "y": 120, "font_size": 26, "color": "#ffffff", "bg_style": "custom", "custom_bg_color": "#18142a", "custom_bg_opacity": 85, "custom_border_color": "#00e676", "custom_border_width": 2, "container_padding": 12, "container_radius": 14, "text_shadow": True, "text_stroke": True, "city": "Тюмень", "icon": "☀" },
                { "type": "active_subscriber", "x": 260, "y": 240, "font_size": 24, "color": "#ffffff", "bg_style": "neon", "period": "day", "container_padding": 12, "container_radius": 16, "text_shadow": True, "text_stroke": True, "label": "Лидер дня:", "avatar_size": 50, "icon": "★" }
            ]
            db.add(bot)
            db.commit()
            
            res = await vk_cover_service.publish_cover(db, bot)
            print("PUBLISH RESULT:", res)

if __name__ == "__main__":
    asyncio.run(test())
