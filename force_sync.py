import asyncio
from app.core.database import SessionLocal
from app.services.iiko_sync_service import IikoSyncService

async def main():
    session = SessionLocal()
    sync_service = IikoSyncService()
    try:
        print("Starting sync...")
        await sync_service.sync_orders(session, hours=48)
        print("Sync complete!")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
