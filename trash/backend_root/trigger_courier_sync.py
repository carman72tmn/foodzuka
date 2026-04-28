import asyncio
import sys
sys.path.insert(0, '/app')
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal

async def main():
    print("Starting courier deliveries sync...")
    with SessionLocal() as session:
        await iiko_sync_service.sync_courier_deliveries(session)
    print("Sync finished.")

if __name__ == "__main__":
    asyncio.run(main())
