import asyncio
from app.core.database import SessionLocal
from app.services.iiko_sync_service import IikoSyncService
from app.models.iiko_settings import IikoSettings

async def main():
    session = SessionLocal()
    sync_service = IikoSyncService()
    try:
        settings = session.query(IikoSettings).first()
        org_id = settings.organization_id
        order_id = "17e5ac36-1cc1-4654-9de8-eaad7cd4709f"
        print(f"Syncing order {order_id} for org {org_id}...")
        res = await sync_service.sync_order_by_id(session, order_id, org_id)
        print(f"Result: {res}")
        
        # Check if address was updated
        from app.models.order import Order
        o = session.query(Order).filter(Order.iiko_order_id == order_id).first()
        if o:
            print(f"New Address: {o.delivery_address}")
            print(f"Street: {o.street}")
            print(f"House: {o.house}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
