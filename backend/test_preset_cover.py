import asyncio
from sqlmodel import Session, select
from app.core.database import engine
from app.services.vk_cover_service import vk_cover_service
from app.models.vk_cover_bot import VkCoverBot

async def test_preset():
    with Session(engine) as db:
        bot = db.exec(select(VkCoverBot)).first()
        if not bot:
            print("No cover bot found!")
            return
        
        print("Setting Premium Preset widgets...")
        bot.widgets = [
            { "type": "clock", "x": 260, "y": 120, "font_size": 28, "color": "#ffffff", "bg_style": "glass", "container_padding": 12, "container_radius": 14, "text_shadow": True, "text_stroke": True, "icon": "⏰", "show_date": True },
            { "type": "weather", "x": 880, "y": 120, "font_size": 26, "color": "#ffffff", "bg_style": "glass", "container_padding": 12, "container_radius": 14, "text_shadow": True, "text_stroke": True, "city": "Тюмень", "icon": "🌤" },
            { "type": "orders_counter", "x": 260, "y": 220, "font_size": 24, "color": "#00e676", "bg_style": "pill", "container_padding": 10, "container_radius": 20, "text_shadow": True, "text_stroke": True, "label": "Сегодня доставлено:", "icon": "🚚" },
            { "type": "promo_code", "x": 880, "y": 220, "font_size": 26, "color": "#ffffff", "bg_style": "gradient", "container_padding": 12, "container_radius": 14, "text_shadow": True, "text_stroke": True, "label": "Промокод дня:", "code": "VK2026", "icon": "🎁" },
            { "type": "active_subscriber", "x": 260, "y": 310, "font_size": 24, "color": "#ffffff", "bg_style": "neon", "container_padding": 12, "container_radius": 16, "text_shadow": True, "text_stroke": True, "label": "Лидер недели:", "avatar_size": 50, "icon": "👑" },
            { "type": "last_winner", "x": 880, "y": 310, "font_size": 22, "color": "#ff9100", "bg_style": "glass", "container_padding": 10, "container_radius": 12, "text_shadow": True, "text_stroke": True, "label": "Победитель игры:", "icon": "🎉" }
        ]
        db.add(bot)
        db.commit()
        db.refresh(bot)

        print("Generating and publishing preset cover image...")
        success = await vk_cover_service.publish_cover(db, bot)
        print(f"Publish result: {success}")

if __name__ == "__main__":
    asyncio.run(test_preset())
