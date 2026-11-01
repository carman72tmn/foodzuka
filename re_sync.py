import asyncio
import sys
import os

# Add /app to path if running inside docker
sys.path.append("/app")

from app.core.database import SessionLocal
from app.services.iiko_sync_service import iiko_sync_service
from app.models.order import Order
from sqlmodel import select

async def run():
    session = SessionLocal()
    # Order 181
    order1 = session.exec(select(Order).where(Order.id == 181)).first()
    if order1:
        print(f"Syncing order 181 (iiko_id: {order1.iiko_order_id})...")
        res1 = await iiko_sync_service.sync_order_by_id(session, order1.branch_id, order1.iiko_order_id)
        print(f"Order 181 sync result: {res1}")
    
    # Order 178
    order2 = session.exec(select(Order).where(Order.id == 178)).first()
    if order2:
        print(f"Syncing order 178 (iiko_id: {order2.iiko_order_id})...")
        res2 = await iiko_sync_service.sync_order_by_id(session, order2.branch_id, order2.iiko_order_id)
        print(f"Order 178 sync result: {res2}")
        
    session.close()

if __name__ == "__main__":
    asyncio.run(run())
