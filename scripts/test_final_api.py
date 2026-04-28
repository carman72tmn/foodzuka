import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta

# Настраиваем логирование ПЕРЕД импортом наших сервисов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("test_final")

# Добавляем путь к приложению для импортов
sys.path.append(os.getcwd())

from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def main():
    logger.info("Testing FINAL get_orders_by_date implementation with STDOUT logging...")
    with SessionLocal() as session:
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login
        org_id = settings_db.organization_id
        
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(hours=48)
        
        logger.info(f"Calling get_orders_by_date for {org_id} from {date_from} to {date_to}...")
        
        try:
            # Вызываем как в iiko_sync_service (без statuses)
            orders = await iiko_service.get_orders_by_date(date_from, date_to, org_id, api_login=api_login)
            
            logger.info(f"SUCCESS! Result: Found {len(orders)} orders/deliveries.")
            if orders:
                logger.info(f"First order ID: {orders[0].get('id')}")
            else:
                logger.warning("No orders found. Check iiko Cloud for orders in last 48h.")
                
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
