"""
Планировщик фоновых задач (APScheduler)
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session
from app.core.database import engine
from app.services.iiko_sync_service import iiko_sync_service

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def sync_shifts_task():
    """Синхронизация смен каждые 15 минут"""
    logger.info("Cron: Запуск синхронизации смен сотрудников...")
    try:
        with Session(engine) as session:
            # Синхронизируем за последние 2 дня для надежности
            await iiko_sync_service.sync_employees_full(session, days=2)
        logger.info("Cron: Синхронизация смен завершена")
    except Exception as e:
        logger.error(f"Cron: Ошибка при синхронизации смен: {e}")

async def sync_orders_task():
    """Синхронизация заказов каждые 10 минут для актуализации статусов"""
    logger.info("Cron: Запуск синхронизации заказов...")
    try:
        with Session(engine) as session:
            # Синхронизируем за последние 24 часа
            await iiko_sync_service.sync_orders(session, hours=24)
        logger.info("Cron: Синхронизация заказов завершена")
    except Exception as e:
        logger.error(f"Cron: Ошибка при синхронизации заказов: {e}")

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(sync_shifts_task, "interval", minutes=15, id="sync_shifts")
        scheduler.add_job(sync_orders_task, "interval", minutes=10, id="sync_orders")
        scheduler.start()
        logger.info("Планировщик запущен (смены: 15 мин, заказы: 10 мин)")
