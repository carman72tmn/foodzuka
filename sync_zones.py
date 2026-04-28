from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal
import asyncio
import logging

# Настройка логов для видимости в консоли
logging.basicConfig(level=logging.INFO)

async def main():
    print("Starting delivery zones sync...")
    # Метод sync_delivery_restrictions является асинхронным и требует session
    try:
        with SessionLocal() as session:
            result = await iiko_sync_service.sync_delivery_restrictions(session)
            print(f"Sync result: {result}")
    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    asyncio.run(main())
