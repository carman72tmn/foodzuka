import asyncio
import logging
from app.core.celery_app import celery_app
from app.services.mailing_cascade_service import mailing_cascade_service

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.mailing_tasks.execute_cascade_step_task")
def execute_cascade_step_task(self, cascade_id: int, step_id: int, order_id: int):
    """
    Задача выполнения шага каскада рассылки.
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        # Запускаем асинхронный метод через event loop
        loop.run_until_complete(
            mailing_cascade_service.execute_step(cascade_id, step_id, order_id)
        )
        return {"status": "success", "step_id": step_id}
    except Exception as e:
        logger.error(f"Error in execute_cascade_step_task: {e}")
        raise e
