import asyncio
from app.core.database import SessionLocal
from app.models.order import Order
from app.services.iiko_sync_service import IikoSyncService
from app.models.iiko_settings import IikoSettings

async def main():
    session = SessionLocal()
    sync_service = IikoSyncService()
    try:
        settings = session.query(IikoSettings).first()
        org_id = settings.organization_id
        
        # Get delivery orders from the last 3 days
        orders = session.query(Order).filter(
            Order.order_type == "Доставка"
        ).order_by(Order.created_at.desc()).limit(100).all()
        
        print(f"Refreshing {len(orders)} delivery orders...")
        for o in orders:
            if o.iiko_order_id:
                print(f"Syncing ID {o.id} ({o.iiko_order_id})...")
                await sync_service.sync_order_by_id(session, str(o.iiko_order_id), org_id)
        
        print("Done!")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
