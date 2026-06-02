import asyncio
import logging
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal

logging.basicConfig(level=logging.INFO)

async def test_stop_lists():
    session = SessionLocal()
    print("Testing stop-list sync...")
    res = await iiko_sync_service.sync_stop_lists(session)
    print(f"Result: {res}")

if __name__ == "__main__":
    asyncio.run(test_stop_lists())
