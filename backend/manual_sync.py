import asyncio
import logging
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    session = SessionLocal()
    print("Starting courier sync for last 7 days...")
    try:
        await iiko_sync_service.sync_courier_deliveries(session, days=7)
        print("Courier sync finished successfully.")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
