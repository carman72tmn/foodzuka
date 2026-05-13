import asyncio
import os
import sys
from datetime import date

sys.path.append(os.getcwd())

from app.services.iiko_sync_service import IikoSyncService
from app.core.database import SessionLocal

async def main():
    sync = IikoSyncService()
    target_date = date(2026, 4, 20)
    print(f"Starting force sync for {target_date}...")
    
    with SessionLocal() as session:
        try:
            await sync.sync_attendance_shifts(session, target_date)
            print("Sync completed successfully.")
        except Exception as e:
            print(f"Sync failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
