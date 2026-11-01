import asyncio
import os
import sys

# Добавляем пути
sys.path.append("/app")

from app.core.database import SessionLocal
from app.models.order import Order
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import iiko_sync_service
from sqlmodel import select

async def main():
    order_id = 1593
    print(f"Starting force sync for order ID {order_id}...")
    session = SessionLocal()
    
    # Ищем заказ в БД
    order = session.exec(select(Order).where(Order.id == order_id)).first()
    if not order:
        print(f"Order {order_id} not found in DB")
        return
        
    print(f"Found order ID: {order.id}, ExtNum: {order.external_number}, IikoID: {order.iiko_order_id}")
    
    if not order.iiko_order_id:
        print("Order has no iiko_order_id, cannot sync via iiko API.")
        return
        
    # Получаем organization_id
    settings_db = session.exec(select(IikoSettings)).first()
    organization_id = settings_db.organization_id if settings_db else None
    if not organization_id:
        print("Organization ID not found in iiko_settings")
        return
        
    print(f"Syncing order {order.iiko_order_id}...")
    success = await iiko_sync_service.sync_order_by_id(session, order.iiko_order_id, organization_id)
    
    if success:
        print("Sync execution successful!")
        # Перезагружаем заказ и смотрим позиции в order_items
        session.refresh(order)
        from app.models.order import OrderItem
        items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        print(f"Successfully synced! Items in order_items table count: {len(items)}")
        for item in items:
            print(f"  - {item.product_name} (ID: {item.product_id}, Kitchen Zone: {item.kitchen_zone_id}, Status: {item.kitchen_status})")
    else:
        print("Sync execution failed.")

if __name__ == "__main__":
    asyncio.run(main())
