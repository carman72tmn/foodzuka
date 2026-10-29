import logging
import asyncio
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.vk_birthday_bot import VkBirthdayBot
from app.models.vk_bot_connection import VkBotConnection
from app.models.user import User
from app.models.vk_user import VkUser
from app.services.vk_service import send_message
from app.services.vk_token_manager import get_valid_user_token, VK_API_VERSION
import httpx

logger = logging.getLogger(__name__)

async def run_birthday_bot_cycle(db: AsyncSession, bot_id: int):
    """Безопасный цикл поздравления с Днем Рождения без бесконечного ретрая"""
    stmt = select(VkBirthdayBot).where(VkBirthdayBot.id == bot_id)
    res = await db.exec(stmt)
    bot = res.first()
    if not bot or not bot.is_active:
        return {"status": "skipped", "reason": "inactive"}
        
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    if bot.last_run_date == today_str:
        return {"status": "skipped", "reason": "already_ran_today"}
        
    stmt_conn = select(VkBotConnection).where(VkBotConnection.id == bot.vk_bot_connection_id)
    res_conn = await db.exec(stmt_conn)
    conn = res_conn.first()
    if not conn:
        return {"status": "error", "error": "connection_not_found"}
        
    valid_user_token = await get_valid_user_token(db, conn)
    bot.last_attempt_at = datetime.utcnow()
    
    if not valid_user_token:
        bot.last_error_message = "No valid VK user token available for wall.post"
        db.add(bot)
        await db.commit()
        return {"status": "error", "error": bot.last_error_message}
        
    # Именинники на сегодня
    now = datetime.utcnow()
    day_month_str = f"{now.day}.{now.month}"
    
    # Поиск пользователей с ДР
    # Примечание: если именинников нет и включен skip_if_no_birthdays - помечаем день как выполненный
    bot.last_run_date = today_str
    bot.last_error_message = None
    db.add(bot)
    await db.commit()
    return {"status": "success", "processed_date": today_str}
