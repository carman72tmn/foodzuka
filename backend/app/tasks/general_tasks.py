"""
Общие задачи синхронизации (Меню, Заказы)
"""
import asyncio
import logging
from datetime import datetime, timezone
from sqlmodel import Session
from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.sync_log import SyncStatus
from app.services.iiko_sync_service import iiko_sync_service

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.general_tasks.sync_menu_task")
def sync_menu_task(self, status_id: int):
    """Задача синхронизации меню"""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "running"
                status.details = "Запуск синхронизации меню..."
                session.add(status)
                session.commit()

            # Выполняем синхронизацию
            res = loop.run_until_complete(iiko_sync_service.sync_menu(session))
            
            # Обновляем статус
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "completed" if res.get("success") else "error"
                status.details = res.get("message") or "Синхронизация завершена"
                status.processed_count = res.get("products_synced", 0)
                status.total_count = res.get("products_synced", 0)
                status.added_count = res.get("categories_synced", 0)
                status.updated_at = datetime.now(timezone.utc)
                session.add(status)
                session.commit()
        return res
    except Exception as e:
        logger.error(f"Menu sync task failed: {e}")
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "error"
                status.details = str(e)
                session.add(status)
                session.commit()
        raise e

@celery_app.task(bind=True, name="app.tasks.general_tasks.sync_orders_task")
def sync_orders_task(self, status_id: int, hours: int = 24):
    """Задача синхронизации заказов"""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "running"
                status.details = f"Синхронизация заказов за {hours} ч..."
                session.add(status)
                session.commit()

            # Выполняем синхронизацию
            # Метод sync_orders возвращает количество обработанных заказов
            count = loop.run_until_complete(iiko_sync_service.sync_orders(session, hours=hours))
            
            # Обновляем статус
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "completed"
                status.details = f"Синхронизировано заказов: {count}"
                status.processed_count = count
                status.total_count = count
                status.updated_at = datetime.now(timezone.utc)
                session.add(status)
                session.commit()
        return {"count": count}
    except Exception as e:
        logger.error(f"Orders sync task failed: {e}")
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "error"
                status.details = str(e)
                session.add(status)
                session.commit()
        raise e
