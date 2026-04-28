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
        
        # Get delivery orders (Доставка)
        delivery_str = "\u0414\u043e\u0441\u0442\u0430\u0432\u043a\u0430"
        orders = session.query(Order).filter(
            Order.order_type == delivery_str
        ).order_by(Order.created_at.desc()).limit(100).all()
        
        print(f"Refreshing {len(orders)} delivery orders...")
        for o in orders:
            if o.iiko_order_id:
                print(f"Syncing ID {o.id}...")
                await sync_service.sync_order_by_id(session, str(o.iiko_order_id), org_id)
        
        print("Done!")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
