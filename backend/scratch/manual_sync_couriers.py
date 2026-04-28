import asyncio
import logging
from datetime import datetime
from app.core.database import SessionLocal
from app.services.iiko_sync_service import IikoSyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    sync_service = IikoSyncService()
    # 22.04.2026
    target_date = datetime(2026, 4, 22)
    
    with SessionLocal() as session:
        logger.info(f"Запуск ручной синхронизации за {target_date.date()}")
        await sync_service.sync_courier_deliveries(
            session=session, 
            date_from=target_date, 
            date_to=target_date
        )
        logger.info("Синхронизация завершена.")

if __name__ == "__main__":
    asyncio.run(main())
