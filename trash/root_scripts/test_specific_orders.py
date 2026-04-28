import asyncio
import os
import sys

# Добавляем путь к приложению
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.order import Order
from app.services.iiko_sync_service import IikoSyncService
from app.models.iiko_settings import IikoSettings

async def sync_specific():
    sync_service = IikoSyncService()
    
    # ID заказов в БД
    target_ids = [358, 357, 356]
    
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Settings not found")
            return
            
        organization_id = settings.organization_id
        
        for oid in target_ids:
            order = session.exec(select(Order).where(Order.id == oid)).first()
            if not order:
                print(f"Order ID {oid} not found in DB")
                continue
                
            print(f"Syncing order ID {oid} (ExtNum: {order.external_number}, iiko_id: {order.iiko_order_id})...")
            try:
                # В вызываемом методе sync_order_by_id вызывается process_iiko_order
                res = await sync_service.sync_order_by_id(session, order.iiko_order_id, organization_id)
                if res:
                    # Проверяем что изменилось
                    session.refresh(order)
                    print(f"  Result: Lat={order.latitude}, Lng={order.longitude}, ZoneID={order.resolved_delivery_zone_id}, Address={order.delivery_address}")
                else:
                    print(f"  Failed to sync from iiko")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(sync_specific())
