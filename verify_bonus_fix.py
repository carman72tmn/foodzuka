import asyncio
from app.core.database import SessionLocal
from app.services.iiko_sync_service import IikoSyncService
from app.models.iiko_settings import IikoSettings
from app.models.order import Order
from sqlalchemy import select

async def main():
    session = SessionLocal()
    sync_service = IikoSyncService()
    try:
        # Order ID from previous check
        iiko_id = "6a6d9c32-cedc-4a0f-a5d4-fe6c49d369cf"
        
        # Get org_id from settings
        settings = session.query(IikoSettings).first()
        org_id = settings.organization_id
        
        print(f"--- BEFORE RE-SYNC ---")
        order_before = session.exec(select(Order).where(Order.iiko_order_id == iiko_id)).first()
        if order_before:
            print(f"Comment: {order_before.comment}")
            print(f"Total: {order_before.total_amount}")
            print(f"Discount: {order_before.total_discount}")
            print(f"With Disc: {order_before.total_with_discount}")
            print(f"Left to Pay: {order_before.left_to_pay}")
            print(f"Bonus Spent: {order_before.bonus_spent}")
        
        print(f"\nSyncing order {iiko_id}...")
        # Force re-sync by pretending it's a webhook or direct sync
        await sync_service.sync_order_by_id(session, iiko_id, org_id)
        
        session.expire_all()
        print(f"\n--- AFTER RE-SYNC ---")
        order_after = session.exec(select(Order).where(Order.iiko_order_id == iiko_id)).first()
        if order_after:
            print(f"Comment: {order_after.comment}")
            print(f"Total: {order_after.total_amount}")
            print(f"Discount: {order_after.total_discount}")
            print(f"With Disc: {order_after.total_with_discount}")
            print(f"Left to Pay: {order_after.left_to_pay}")
            print(f"Bonus Spent: {order_after.bonus_spent}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
