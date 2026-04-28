import asyncio
import sys
import os
import logging

sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
from app.core.database import engine
from app.services.revenue_sync import revenue_sync_service

async def run_sync():
    print("Triggering revenue sync for yesterday...")
    await revenue_sync_service.sync_period("yesterday")
    print("Done.")

if __name__ == "__main__":
    asyncio.run(run_sync())
