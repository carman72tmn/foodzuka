import os
import sys
import asyncio

# Добавляем путь к backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import SessionLocal
from app.services.iiko_sync_service import iiko_sync_service

async def run():
    session = SessionLocal()
    try:
        print("Starting sync_orders(hours=24)...")
        await iiko_sync_service.sync_orders(session, hours=24)
        print("Sync complete!")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run())
