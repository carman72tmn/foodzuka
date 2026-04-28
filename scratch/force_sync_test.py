import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к приложению
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.config import settings
from app.services.iiko_sync_service import IikoSyncService
from app.services.iiko_service import iiko_service
from app.models.iiko_settings import IikoSettings
from sqlmodel import Session, create_engine, select

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Используем URL из конфига
engine = create_engine(settings.DATABASE_URL)

async def main():
    sync_service = IikoSyncService()
    
    with Session(engine) as session:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db:
            logger.error("Iiko settings not found in database")
            return
            
        org_id = settings_db.organization_id
        api_login = settings_db.api_login
        
        # Период для проверки (22-24 апреля 2026)
        # ВНИМАНИЕ: Используем UTC или локальное время в зависимости от настроек
        date_from = datetime(2026, 4, 22)
        date_to = datetime(2026, 4, 25)
        
        logger.info(f"=== Starting Force Sync Test ===")
        logger.info(f"Organization ID: {org_id}")
        logger.info(f"Period: {date_from} to {date_to}")
        
        # 0. Отладка: Список доступных колонок OLAP
        logger.info("--- Testing OLAP Columns ---")
        try:
            cols_resp = await iiko_service._resto_request("GET", "/api/0/olaps/olapColumns?reportType=SALES", organization_id=org_id)
            # logger.info(f"Available SALES columns: {cols_resp}")
            # Ищем что-то похожее на Discount или Sum
            import json
            # cols = json.loads(cols_resp) if isinstance(cols_resp, str) else cols_resp
            # logger.info(f"Columns: {cols}")
        except Exception as e:
            logger.error(f"Failed to get OLAP columns: {e}")

        # 1. Тест OLAP (Проверка исправления 422 ошибки)
        logger.info("--- Testing OLAP Report (Revenue) ---")
        try:
            revenue_data = await iiko_service.get_daily_revenue_olap(
                date_from=date_from,
                date_to=date_to,
                organization_id=org_id,
                api_login=api_login
            )
            logger.info(f"OLAP Revenue Success! Data keys: {list(revenue_data.keys())}")
        except Exception as e:
            logger.error(f"OLAP Revenue Failed: {e}")

        # 1.5 Тест отчета по курьерам
        logger.info("--- Testing Courier Deliveries Report ---")
        try:
            deliveries = await iiko_service.get_resto_detailed_deliveries(
                date_from=date_from,
                date_to=date_to,
                organization_id=org_id
            )
            logger.info(f"Courier Report Success! Count: {len(deliveries)}")
            if deliveries:
                logger.info(f"Sample delivery: {deliveries[0]}")
                logger.info(f"Customer Name: {deliveries[0].get('customer', {}).get('name')}, Phone: {deliveries[0].get('customer', {}).get('phone')}")
        except Exception as e:
            logger.error(f"Courier Report Failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # 2. Тест синхронизации заказов (Проверка format_address и UnboundLocalError)
        logger.info("--- Testing Order Sync & Address Formatting ---")
        try:
            orders = await iiko_service.get_orders_by_date(
                date_from=date_from,
                date_to=date_to,
                organization_id=org_id,
                api_login=api_login
            )
            logger.info(f"Fetched {len(orders)} orders from Iiko Cloud")
            
            if orders:
                test_order = orders[0]
                logger.info(f"Processing test order: {test_order.get('id')}")
                
                # Проверяем format_address отдельно
                addr_data = test_order.get('deliveryPoint', {}).get('address', {})
                formatted = sync_service.format_address(addr_data, fmt="line1")
                logger.info(f"Formatted Address (line1): {formatted}")
                
                # Пробуем полный процесс синхронизации одного заказа
                await sync_service.process_iiko_order(session, test_order, org_id)
                logger.info("Order processed successfully (no UnboundLocalError)")
            else:
                logger.warning("No orders found for this period to test processing")
                
        except Exception as e:
            logger.error(f"Order Sync Test Failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

    logger.info("=== Force Sync Test Completed ===")

if __name__ == "__main__":
    asyncio.run(main())
