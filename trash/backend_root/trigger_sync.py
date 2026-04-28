import asyncio
import sys
import os
import logging

# Add the project directory to sys.path
sys.path.append(os.getcwd())

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Silence noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

from app.core.database import Session, engine
from app.services.iiko_sync_service import iiko_sync_service

async def run_sync():
    print("Starting manual sync of orders for last 48 hours...")
    try:
        with Session(engine) as session:
            await iiko_sync_service.sync_orders(session, hours=48)
            print("Sync process finished.")
    except Exception as e:
        print(f"Sync failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_sync())
