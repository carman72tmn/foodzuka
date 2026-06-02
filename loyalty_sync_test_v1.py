import asyncio
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal

async def run_loyalty_sync():
    print("Starting loyalty sync...")
    with SessionLocal() as session:
        try:
            res = await iiko_sync_service.sync_loyalty_items(session)
            print(f"Result: {res}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_loyalty_sync())
