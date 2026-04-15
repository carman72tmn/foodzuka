import asyncio
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.services.iiko_service import iiko_service
from app.services.iiko_sync_service import iiko_sync_service
from app.models.iiko_settings import IikoSettings

async def sync_recent():
    sync_service = iiko_sync_service
    
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings or not settings.organization_id:
            print("Settings not found")
            return
            
        org_id = settings.organization_id
        now = datetime.utcnow()
        date_from = now - timedelta(days=1)
        date_to = now + timedelta(hours=1)
        
        print(f"Fetching orders from {date_from} to {date_to}...")
        
        try:
            # Используем исправленный метод _request через get_orders_by_date
            orders = await iiko_service.get_orders_by_date(date_from, date_to, organization_id=org_id)
            print(f"Found {len(orders)} orders in iiko Cloud for last 24h")
            
            for o_summary in orders:
                order_id = o_summary.get("id")
                print(f"Syncing order {order_id}...")
                success = await sync_service.sync_order_by_id(session, order_id, org_id)
                print(f"  Result: {'Success' if success else 'Failed'}")
                
            session.commit()
        except Exception as e:
            print(f"Error during sync: {e}")

if __name__ == "__main__":
    asyncio.run(sync_recent())
