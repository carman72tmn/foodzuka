import asyncio
import argparse
import os
import sys

# Добавляем путь к корню приложения, чтобы импорты работали
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.iiko_service import iiko_service
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import Session, engine

async def sync_order(order_id: str):
    print(f"Syncing order {order_id}...")
    
    # Получаем organization_id из настроек или iiko_service
    organization_id = iiko_service.organization_id
    if not organization_id:
        print("Error: organization_id not found in iiko_service")
        return

    try:
        with Session(engine) as session:
            # Используем встроенный метод синхронизации по ID
            success = await iiko_sync_service.sync_order_by_id(session, order_id, organization_id)
            if success:
                session.commit()
                print(f"Order {order_id} successfully synced.")
            else:
                print(f"Failed to sync order {order_id}.")

    except Exception as e:
        print(f"Error during sync: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync a single order from iiko')
    parser.add_argument('--order_id', type=str, required=True, help='ID of the order in iiko')
    args = parser.parse_args()
    
    asyncio.run(sync_order(args.order_id))
