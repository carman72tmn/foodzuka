from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal
import asyncio
import json

async def main():
    print("Minimal sync test starting...")
    session = SessionLocal()
    try:
        result = await iiko_sync_service.sync_delivery_restrictions(session)
        print("RESULT_START")
        print(json.dumps(result))
        print("RESULT_END")
    except Exception as e:
        print(f"FAILED with exception: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
