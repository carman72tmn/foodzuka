
import os
import sys
import asyncio
from datetime import datetime, timedelta
import logging

# Setup logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add app path
sys.path.append("/app")

from app.core.database import Session, engine
from app.services.iiko_sync_service import iiko_sync_service
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def trigger():
    with Session(engine) as session:
        print("Starting manual courier deliveries sync...")
        # Sync for last 3 days for testing
        await iiko_sync_service.sync_courier_deliveries(session, days=3)
        print("Sync finished.")

if __name__ == "__main__":
    asyncio.run(trigger())
