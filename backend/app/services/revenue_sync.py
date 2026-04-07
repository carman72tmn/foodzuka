import asyncio
import logging
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session, select

from app.core.database import engine, get_session
from app.models.iiko_settings import IikoSettings
from app.models.olap_revenue import OlapRevenueRecord
from app.services.iiko_service import iiko_service

logger = logging.getLogger(__name__)

class RevenueSyncService:
    """Сервис для автоматической синхронизации выручки из iiko"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def start(self):
        if self._is_running:
            return
        
        # Добавляем задачу каждые 30 минут
        self.scheduler.add_job(
            self.sync_today_revenue,
            IntervalTrigger(minutes=30),
            id="sync_today_revenue",
            name="Синхронизация выручки за сегодня (каждые 30 мин)",
            replace_existing=True
        )
        
        # Дополнительная задача в полночь для окончательного закрытия предыдущего дня
        self.scheduler.add_job(
            self.sync_yesterday_revenue,
            CronTrigger(hour=0, minute=5),
            id="sync_yesterday_revenue",
            name="Финальная синхронизация за вчера",
            replace_existing=True
        )

        self.scheduler.start()
        self._is_running = True
        logger.info("Планировщик синхронизации выручки запущен (интервал 30 мин)")

    async def sync_today_revenue(self):
        """Синхронизация выручки за текущий день"""
        logger.info("Запуск плановой синхронизации выручки за сегодня...")
        await self.sync_period("today")

    async def sync_yesterday_revenue(self):
        """Синхронизация выручки за вчерашний день (для точности логов)"""
        logger.info("Запуск плановой синхронизации выручки за вчера...")
        await self.sync_period("yesterday")

    async def sync_period(self, period: str):
        """Общая логика синхронизации выручки за период"""
        from app.api.reports import _get_period_dates
        
        try:
            date_from, date_to = _get_period_dates(period, None, None)
            
            with Session(engine) as db:
                settings = db.exec(select(IikoSettings)).first()
                if not settings:
                    logger.warning("Синхронизация выручки отменена: настройки iiko не найдены")
                    return

                # Получаем данные из iiko (метод сам выберет Office/Cloud)
                try:
                    rows = await iiko_service.get_olap_report(
                        date_from=date_from,
                        date_to=date_to,
                        api_login=settings.api_login,
                        organization_id=settings.organization_id,
                        include_deleted=False,
                        resto_url=settings.resto_url,
                        resto_login=settings.resto_login,
                        resto_password=settings.resto_password,
                    )
                except Exception as e:
                    logger.error(f"Ошибка получения данных OLAP при синхронизации: {e}")
                    return

                if not rows:
                    logger.info(f"Синхронизация {period}: данных не получено")
                    return

                # Удаляем старые записи за этот период типа 'today' или 'yesterday'
                # В нашей модели мы используем period_type для кэширования
                old_records = db.exec(
                    select(OlapRevenueRecord).where(
                        OlapRevenueRecord.period_type == period,
                        OlapRevenueRecord.date_from >= date_from,
                        OlapRevenueRecord.date_to <= date_to
                    )
                ).all()
                for old in old_records:
                    db.delete(old)
                db.commit()

                # Сохраняем новые данные
                for row in rows:
                    record = OlapRevenueRecord(
                        organization_id=settings.organization_id,
                        organization_name=row.get("organization_name", ""),
                        date_from=date_from,
                        date_to=date_to,
                        business_date=row.get("business_date"),
                        period_type=period,
                        average_check=row.get("average_check", 0.0),
                        markup=row.get("markup", 0.0),
                        markup_percent=row.get("markup_percent", 0.0),
                        cost_price=row.get("cost_price", 0.0),
                        cost_price_percent=row.get("cost_price_percent", 0.0),
                        discount_sum=row.get("discount_sum", 0.0),
                        revenue=row.get("revenue", 0.0),
                        orders_count=row.get("orders_count", 0),
                        include_deleted=False,
                        updated_at=datetime.utcnow(),
                    )
                    db.add(record)
                db.commit()
                logger.info(f"Синхронизация выручки {period} успешно завершена. Записей: {len(rows)}")

        except Exception as e:
            logger.error(f"Критическая ошибка при синхронизации выручки {period}: {e}", exc_info=True)

# Глобальный экземпляр
revenue_sync_service = RevenueSyncService()
