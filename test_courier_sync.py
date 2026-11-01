import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add /app to path if running inside docker
sys.path.append("/app")

from app.core.database import SessionLocal
from app.services.iiko_sync_service import iiko_sync_service
from sqlmodel import select

async def run():
    session = SessionLocal()
    print("Starting manual courier delivery sync for last 3 days...")
    try:
        # sync_courier_deliveries(session, days=3)
        await iiko_sync_service.sync_courier_deliveries(session, days=3)
        print("Sync task finished.")
    except Exception as e:
        print(f"Sync failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run())
