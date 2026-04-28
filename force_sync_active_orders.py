import os
import asyncio
import sys
from datetime import datetime, timedelta

# Добавляем путь к backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import SessionLocal
from app.models.order import Order
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import iiko_sync_service
from sqlmodel import select

async def force_sync_active_orders():
    print("Starting force sync of active orders...")
    session = SessionLocal()
    try:
        settings = session.exec(select(IikoSettings)).first()
        if not settings or not settings.organization_id:
            print("Iiko settings not found!")
            return

        org_id = settings.organization_id
        
        # Находим заказы, которые не закрыты и не отменены
        active_statuses = ['WAIT_COOKING', 'COOKING', 'WAITING', 'ON_WAY', 'DELIVERED', 'NEW', 'PAYMENT_PENDING']
        query = select(Order).where(Order.status.in_(active_statuses))
        active_orders = session.exec(query).all()
        
        print(f"Found {len(active_orders)} active orders in DB.")
        
        success_count = 0
        for order in active_orders:
            if not order.iiko_order_id:
                print(f"Order {order.external_number} has no iiko_order_id, skipping.")
                continue
                
            print(f"Syncing order {order.external_number} (iiko_id: {order.iiko_order_id})...")
            try:
                res = await iiko_sync_service.sync_order_by_id(session, str(order.iiko_order_id), org_id)
                if res:
                    # Перечитываем заказ, чтобы увидеть новый статус
                    session.refresh(order)
                    print(f"  Result: Status={order.status}")
                    success_count += 1
                else:
                    print(f"  Result: Failed to fetch from iiko")
            except Exception as e:
                print(f"  Error syncing order {order.external_number}: {e}")
        
        print(f"Finished. Synced {success_count} orders.")
        
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(force_sync_active_orders())
