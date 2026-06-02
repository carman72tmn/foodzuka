import asyncio
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import Session, engine

async def run_manual_sync():
    print("Starting manual courier sync...")
    with Session(engine) as session:
        await iiko_sync_service.sync_courier_deliveries(session, days=1)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(run_manual_sync())
