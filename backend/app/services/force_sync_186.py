
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import get_session_sync, Session, engine
from app.models.order import Order
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import iiko_sync_service
from app.services.iiko_service import iiko_service
from sqlmodel import select

async def force_sync():
    with get_session_sync() as session:
        # Find order 186
        result = session.exec(select(Order).where(Order.id == 186))
        order = result.first()
        
        if not order:
            print("Order 186 not found in DB")
            return
            
        print(f"Found order: ID={order.id}, ExtNum={order.external_number}, IikoID={order.iiko_order_id}")
        
        if not order.iiko_order_id:
            print("Order has no iiko_order_id, cannot sync")
            return
            
        # Get organization_id from settings
        settings_db = session.exec(select(IikoSettings)).first()
        organization_id = settings_db.organization_id if settings_db else None
            
        if not organization_id:
            print("Organization ID not found in iiko_settings")
            return
            
        print(f"Syncing order {order.iiko_order_id} for organization {organization_id}...")
        # sync_order_by_id is async, so we await it
        success = await iiko_sync_service.sync_order_by_id(session, order.iiko_order_id, organization_id)
        
        if success:
            # get_session_sync will commit on exit, but we can do it explicitly or flush
            print("Order successfully synced!")
            # Refresh from DB
            session.add(order)
            session.refresh(order)
            print(f"New Paid: {order.total_paid}")
            print(f"New Left: {order.left_to_pay}")
        else:
            print("Sync failed.")

if __name__ == "__main__":
    asyncio.run(force_sync())
