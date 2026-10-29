import asyncio
import logging
from sqlmodel import Session
from app.core.celery_app import celery_app
from app.core.database import engine
from app.services.vk_birthday_service import vk_birthday_service

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.vk_birthday_task.vk_birthday_publish_task")
def vk_birthday_publish_task():
    """Задача проверки и публикации поздравлений именинников"""
    logger.info("Starting VK birthday publish task...")
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        with Session(engine) as session:
            loop.run_until_complete(vk_birthday_service.run_birthday_bots_autopublish(session))
        return {"status": "success"}
    except Exception as e:
        logger.error(f"VK birthday publish task failed: {e}", exc_info=True)
        raise e


@celery_app.task(name="app.tasks.vk_birthday_task.vk_birthday_delete_task")
def vk_birthday_delete_task():
    """Задача проверки и удаления просроченных постов поздравлений"""
    logger.info("Starting VK birthday delete task...")
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        with Session(engine) as session:
            loop.run_until_complete(vk_birthday_service.run_birthday_posts_autodelete(session))
        return {"status": "success"}
    except Exception as e:
        logger.error(f"VK birthday delete task failed: {e}", exc_info=True)
        raise e
