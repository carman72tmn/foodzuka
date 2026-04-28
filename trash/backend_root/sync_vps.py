import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append("/app")

# Внутри контейнера импорты идут без префикса 'app'
from db.session import SessionLocal
from services.iiko_sync_service import IikoSyncService

async def run_sync():
    print("Starting manual sync for last 24 hours...")
    sync_service = IikoSyncService()
    session = SessionLocal()
    try:
        result = await sync_service.sync_orders(session, hours=24)
        print(f"Sync result: {result}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run_sync())
