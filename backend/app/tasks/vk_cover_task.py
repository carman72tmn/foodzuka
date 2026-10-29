import asyncio
import logging
from typing import Optional, List
import pytz
from datetime import datetime

from sqlmodel import Session, select
from app.core.celery_app import celery_app
from app.core.database import engine
from app.services.vk_cover_service import vk_cover_service
from app.models.vk_cover_bot import VkCoverBot
from app.models.vk_bot_connection import VkBotConnection

logger = logging.getLogger(__name__)


def should_update_cover(bot: VkCoverBot, now_local: datetime, app_tz: pytz.BaseTzInfo) -> bool:
    """Проверяет, пришло ли время обновлять обложку"""
    if not bot.last_published_at:
        return True
        
    last_pub = bot.last_published_at.replace(tzinfo=pytz.UTC).astimezone(app_tz)
    diff = now_local - last_pub
    diff_minutes = diff.total_seconds() / 60.0
    
    # Если в обложке включено слайд-шоу, проверяем интервал слайд-шоу
    if bot.slideshow_images and len(bot.slideshow_images) > 0:
        slide_interval = max(1, bot.slideshow_interval_minutes or 5)
        if diff_minutes >= slide_interval:
            return True

    interval = bot.update_interval or "1m"
    
    if interval == "callback":
        return diff_minutes >= 60.0
    elif interval == "1m":
        return diff_minutes >= 1.0
    elif interval == "2m":
        return diff_minutes >= 2.0
    elif interval == "3m":
        return diff_minutes >= 3.0
    elif interval == "5m":
        return diff_minutes >= 5.0
    elif interval == "15m":
        return diff_minutes >= 15.0
    elif interval == "30m":
        return diff_minutes >= 30.0
    elif interval == "1h":
        return diff_minutes >= 60.0
    elif interval == "6h":
        return diff_minutes >= 360.0
    elif interval == "12h":
        return diff_minutes >= 720.0
    elif interval == "morning":
        if not (0 <= now_local.hour < 11):
            return False
        return diff_minutes >= 5.0
    elif interval == "day":
        if not (11 <= now_local.hour < 16):
            return False
        return diff_minutes >= 5.0
    elif interval == "evening":
        if not (16 <= now_local.hour <= 23):
            return False
        return diff_minutes >= 5.0
        
    return True


def select_cover_for_rotation(covers: List[VkCoverBot], now_local: datetime) -> Optional[VkCoverBot]:
    """Выбирает наиболее подходящую обложку из активных обложек подключения на основе расписания и порядка"""
    if not covers:
        return None
        
    current_time_str = now_local.strftime("%H:%M")
    
    # 1. Приоритет обложка по строгому диапазону времени
    for bot in covers:
        if bot.is_rotation_enabled and bot.schedule_type == "time_range" and bot.schedule_start_time and bot.schedule_end_time:
            start = bot.schedule_start_time
            end = bot.schedule_end_time
            if start <= end:
                if start <= current_time_str < end:
                    return bot
            else: # Ночной диапазон (например 22:00 - 06:00)
                if current_time_str >= start or current_time_str < end:
                    return bot
                    
    # 2. Фильтруем обложки для универсальной или интервальной ротации
    eligible = [b for b in covers if b.is_rotation_enabled and b.schedule_type in ("always", "interval", None)]
    if eligible:
        eligible.sort(key=lambda b: (b.rotation_order, b.id))
        minute_bucket = (now_local.hour * 60 + now_local.minute) // 15
        idx = minute_bucket % len(eligible)
        return eligible[idx]
        
    return covers[0]


@celery_app.task(name="app.tasks.vk_cover_task.vk_cover_update_task")
def vk_cover_update_task():
    """Периодическая задача обновления динамических обложек ВК для активных ботов"""
    logger.info("Starting VK dynamic cover update task...")
    
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        updated_count = 0
        
        with Session(engine) as session:
            app_tz = vk_cover_service.get_app_timezone(session)
            now_local = datetime.now(app_tz)

            # Находим всех активных ботов обложек
            bots = session.exec(select(VkCoverBot).where(VkCoverBot.is_active == True)).all()
            
            # Группируем обложки по подключению ВК
            grouped = {}
            for bot in bots:
                grouped.setdefault(bot.vk_bot_connection_id, []).append(bot)
                
            for conn_id, conn_bots in grouped.items():
                selected_bot = select_cover_for_rotation(conn_bots, now_local)
                if selected_bot and should_update_cover(selected_bot, now_local, app_tz):
                    logger.info(f"Updating cover '{selected_bot.name}' (id: {selected_bot.id}) for connection: {conn_id} in tz {app_tz}")
                    loop.run_until_complete(vk_cover_service.publish_cover(session, selected_bot))
                    updated_count += 1
                else:
                    logger.debug(f"Skipping cover update for connection: {conn_id}")
                    
        return {"status": "success", "updated_bots_count": updated_count}
    except Exception as e:
        logger.error(f"VK cover update task failed: {e}", exc_info=True)
        raise e


@celery_app.task(name="app.tasks.vk_cover_task.vk_cover_activity_sync_task")
def vk_cover_activity_sync_task():
    """Задача расчета и кэширования активности подписчиков в группах с обложками"""
    logger.info("Starting VK cover activity sync task...")
    
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        with Session(engine) as session:
            bots = session.exec(select(VkCoverBot).where(VkCoverBot.is_active == True)).all()
            processed_groups = set()
            for bot in bots:
                conn = session.get(VkBotConnection, bot.vk_bot_connection_id)
                if conn and conn.is_active and conn.vk_group_id not in processed_groups:
                    processed_groups.add(conn.vk_group_id)
                    logger.info(f"Recalculating subscriber activity for group {conn.vk_group_id}...")
                    loop.run_until_complete(
                        vk_cover_service.update_subscriber_activity(
                            session, conn.vk_group_id, conn.vk_bot_token
                        )
                    )
        return {"status": "success", "processed_groups_count": len(processed_groups)}
    except Exception as e:
        logger.error(f"VK cover activity sync task failed: {e}", exc_info=True)
        raise e
