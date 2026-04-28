import asyncio
from app.core.database import engine
from app.services.iiko_sync_service import iiko_sync_service
from sqlmodel import Session
import logging
import sys

# Настройка логирования чтобы видеть что происходит внутри iiko_sync_service
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def debug_sync():
    print("Starting debug sync...")
    with Session(engine) as session:
        try:
            # Синхронизируем за последние 5 дней (с 20 по 24 апреля)
            await iiko_sync_service.sync_courier_deliveries(session, days=5)
            session.commit()
            print("Sync completed successfully.")
        except Exception as e:
            print(f"Sync failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_sync())
