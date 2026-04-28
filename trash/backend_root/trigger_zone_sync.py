import asyncio
import sys
sys.path.insert(0, '/app')
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal

async def main():
    print("Starting delivery zones sync...")
    with SessionLocal() as session:
        result = await iiko_sync_service.sync_delivery_restrictions(session)
        print(f"Result: {result}")
    print("Sync finished.")

if __name__ == "__main__":
    asyncio.run(main())
