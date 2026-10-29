import logging
from app.core.celery_app import celery_app
from sqlmodel import Session
from app.core.database import engine
from app.services.vk_scheduler_service import vk_scheduler_service

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.vk_scheduler_task.run_vk_post_scheduler")
def run_vk_post_scheduler():
    """Фоновая Celery-задача для проверки и отправки отложенных публикаций ВК"""
    logger.info("Celery Task: Running VK Post Scheduler checks...")
    import asyncio
    
    async def run_async():
        with Session(engine) as db:
            await vk_scheduler_service.check_and_publish_pending(db)
            
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(run_async())
    logger.info("Celery Task: VK Post Scheduler run finished.")
