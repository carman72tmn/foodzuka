import asyncio
import sys
import os
import logging

sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
from app.core.database import Session, engine
from app.services.iiko_sync_service import iiko_sync_service

async def run_sync():
    print("Triggering courier deliveries sync for yesterday...")
    with Session(engine) as session:
        await iiko_sync_service.sync_courier_deliveries(session, days=2)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(run_sync())
