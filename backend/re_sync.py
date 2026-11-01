import asyncio
import sys
import os

# Add /app to path if running inside docker
sys.path.append("/app")

from app.core.database import SessionLocal
from app.services.iiko_sync_service import iiko_sync_service
from app.models.order import Order
from app.models.company import Company, Branch
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def run():
    session = SessionLocal()
    
    # Get default org_id
    settings_db = session.exec(select(IikoSettings)).first()
    default_org_id = settings_db.organization_id if settings_db else "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    # Orders to sync
    target_ids = [181, 178]
    
    for oid in target_ids:
        order = session.exec(select(Order).where(Order.id == oid)).first()
        if order:
            # Try to get org_id from branch -> company
            org_id = None
            if order.branch:
                # Need to refresh or join company
                branch = session.get(Branch, order.branch_id)
                if branch and branch.company:
                    org_id = branch.company.iiko_organization_id
            
            if not org_id:
                org_id = default_org_id
                
            print(f"Syncing order {oid} (iiko_id: {order.iiko_order_id}) for org {org_id}...")
            res = await iiko_sync_service.sync_order_by_id(session, order.iiko_order_id, org_id)
            print(f"Order {oid} sync result: {res}")
            
            # Re-fetch and check values
            session.refresh(order)
            print(f"Order {oid} updated values: TotalWithDiscount={order.total_with_discount}, BaseAmount={order.base_amount}, IsPaid={order.is_paid}")
            if order.discounts_details:
                print(f"Discounts: {order.discounts_details}")
        else:
            print(f"Order {oid} not found in DB")
        
    session.close()

if __name__ == "__main__":
    asyncio.run(run())
