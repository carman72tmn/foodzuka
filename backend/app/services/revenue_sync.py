import asyncio
import logging
from datetime import date
from app.core.datetime_utils import utc_now
from sqlmodel import Session, select

from app.core.database import engine, get_session
from app.models.iiko_settings import IikoSettings
from app.models.olap_revenue import OlapRevenueRecord
from app.services.iiko_service import iiko_service

logger = logging.getLogger(__name__)

class RevenueSyncService:
    """Сервис для синхронизации выручки из iiko (вызывается планировщиком)"""
    
    def __init__(self):
        self._is_running = False

    async def sync_today_revenue(self):
        """Синхронизация выручки за текущий день"""
        logger.info("Запуск плановой синхронизации выручки за сегодня...")
        await self.sync_period("today")

    async def sync_yesterday_revenue(self):
        """Синхронизация выручки за вчерашний день (для точности логов)"""
        logger.info("Запуск плановой синхронизации выручки за вчера...")
        await self.sync_period("yesterday")

    async def sync_period(self, period: str, date_from_custom=None, date_to_custom=None):
        """Общая логика синхронизации выручки за период"""
        # Ленивый импорт для предотвращения циклических зависимостей
        try:
            from app.api.reports import _get_period_dates
        except ImportError:
            # Фолбэк если не удалось импортировать
            from datetime import datetime, timedelta
            def _get_period_dates(p, f, t):
                today = date.today()
                if p == "today": return today, today
                if p == "yesterday": return today - timedelta(days=1), today - timedelta(days=1)
                return today, today
        
        try:
            if date_from_custom and date_to_custom:
                date_from, date_to = date_from_custom, date_to_custom
            else:
                date_from, date_to = _get_period_dates(period, None, None)
            
            with Session(engine) as db:
                settings_obj = db.exec(select(IikoSettings)).first()
                if not settings_obj:
                    logger.warning("Синхронизация выручки отменена: настройки iiko не найдены")
                    return
                
                # Извлекаем все нужные данные СРАЗУ
                api_login = settings_obj.api_login
                org_id = settings_obj.organization_id
                resto_url = settings_obj.resto_url
                resto_login = settings_obj.resto_login
                resto_password = settings_obj.resto_password

                # Получаем данные из iiko
                try:
                    rows = await iiko_service.get_olap_report(
                        date_from=date_from,
                        date_to=date_to,
                        api_login=api_login,
                        organization_id=org_id,
                        include_deleted=False,
                        resto_url=resto_url,
                        resto_login=resto_login,
                        resto_password=resto_password,
                    )
                except Exception as e:
                    logger.error(f"Ошибка получения данных OLAP при синхронизации: {e}")
                    return

                if not rows:
                    logger.info(f"Синхронизация {period}: данных не получено")
                    return

                # Получаем данные по оплатам
                payment_rows = []
                try:
                    payment_rows = await iiko_service.get_payment_types_report(
                        date_from=date_from,
                        date_to=date_to,
                        organization_id=org_id
                    )
                except Exception as pe:
                    logger.warning(f"Не удалось получить данные по типам оплат: {pe}")

                # Удаляем старые записи за этот период
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
                    term = row.get("terminal", "")
                    row_date = row.get("date", "")
                    
                    cash = 0.0
                    card = 0.0
                    online = 0.0
                    
                    for p_row in payment_rows:
                        p_date = str(p_row.get("OpenDate.Typed", "")).split("T")[0]
                        p_term = p_row.get("CashRegisterName", p_row.get("Terminal", ""))
                        
                        if p_date == row_date and (not term or p_term == term):
                            ptype = str(p_row.get("PayTypes", "")).lower()
                            psum = float(p_row.get("fullSum", 0))
                            
                            if any(kw in ptype for kw in ["карт", "visa", "master", "безналич", "эквайринг"]):
                                card += psum
                            elif "налич" in ptype:
                                cash += psum
                            elif any(kw in ptype for kw in ["сайт", "onlin", "cloud", "интернет"]):
                                online += psum
                    
                    record = OlapRevenueRecord(
                        organization_id=org_id,
                        organization_name=row.get("department", org_id),
                        terminal_name=term,
                        date_from=date_from,
                        date_to=date_to,
                        business_date=row_date,
                        period_type=period,
                        average_check=row.get("average_check", 0.0),
                        markup=row.get("markup", 0.0),
                        markup_percent=row.get("markup_percent", 0.0),
                        cost_price=row.get("cost_price", 0.0),
                        cost_price_percent=row.get("cost_price_percent", 0.0),
                        discount_sum=row.get("discount_sum", 0.0),
                        revenue=row.get("revenue", 0.0),
                        orders_count=row.get("orders_count", 0),
                        cash_sum=cash,
                        card_sum=card,
                        online_sum=online,
                        bonus_sum=row.get("bonus_sum", 0.0),
                        include_deleted=False,
                        updated_at=utc_now(),
                    )
                    db.add(record)
                db.commit()
                logger.info(f"Синхронизация выручки {period} успешно завершена. Записей: {len(rows)}")

        except Exception as e:
            logger.error(f"Критическая ошибка при синхронизации выручки {period}: {e}", exc_info=True)

# Глобальный экземпляр
revenue_sync_service = RevenueSyncService()

# Точки входа для планировщика (Entry Points)
async def sync_today_revenue_task():
    """Синхронизация выручки за сегодня"""
    await revenue_sync_service.sync_today_revenue()

async def sync_yesterday_revenue_task():
    """Синхронизация выручки за вчера"""
    await revenue_sync_service.sync_yesterday_revenue()
