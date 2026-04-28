import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append("/app")

# Важно: внутри контейнера пакет называется просто 'db', 'services' и т.д.
# или 'app.db', если корень выше. Попробуем оба варианта
try:
    from db.session import SessionLocal
    from services.iiko_sync_service import IikoSyncService
except ImportError:
    from app.db.session import SessionLocal
    from app.services.iiko_sync_service import IikoSyncService

from sqlalchemy.orm import Session

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
