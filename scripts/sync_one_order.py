import asyncio
import os
import sys

# Добавляем путь к приложению для импортов
sys.path.append(os.getcwd())

from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal

async def main():
    order_id = "a5b96639-44a7-4f46-ae7b-ac997772c1f4"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    print(f"Testing individual sync for order {order_id}...")
    
    with SessionLocal() as session:
        try:
            # Метод sync_order_by_id вызывает get_order_status и затем process_iiko_order
            result = await iiko_sync_service.sync_order_by_id(session, order_id, org_id)
            print(f"Sync result: {result}")
        except Exception as e:
            print(f"Sync failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
