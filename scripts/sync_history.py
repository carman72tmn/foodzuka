import asyncio
import os
import sys

# Добавляем путь к приложению для импортов
sys.path.append(os.getcwd())

from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal

async def main():
    print("Starting mass order sync for last 720 hours (30 days)...")
    with SessionLocal() as session:
        try:
            result = await iiko_sync_service.sync_orders(session, hours=720)
            print(f"Sync completed: {result}")
        except Exception as e:
            print(f"Sync failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
