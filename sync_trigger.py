import asyncio
import os
import sys
from datetime import datetime

# Add app directory to path
sys.path.append('/app')

from app.services.iiko_sync_service import IikoSyncService
from app.core.database import SessionLocal

async def main():
    print(f"[{datetime.now()}] Starting manual MASS sync (date-based)...")
    db = SessionLocal()
    try:
        service = IikoSyncService()
        # sync_orders() triggers the full logic (polling by date)
        await service.sync_orders(db)
        print(f"[{datetime.now()}] Sync finished.")
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(main())
