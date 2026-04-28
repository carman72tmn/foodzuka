import asyncio
import logging
from app.services.iiko_service import iiko_service
from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings

logging.basicConfig(level=logging.INFO)

async def test():
    with Session(engine) as session:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db:
            print("Settings not found")
            return
        
        org_id = settings_db.organization_id
        print(f"Testing recovery logic for org: {org_id}")
        
        try:
            from app.services.iiko_sync_service import iiko_sync_service
            # Вызовем sync_orders напрямую и посмотрим, что там внутри заказов
            from app.services.iiko_service import iiko_service
            from datetime import datetime, timedelta
            date_to = datetime.now()
            date_from = date_to - timedelta(hours=2)
            orders = await iiko_service.get_orders_by_date(date_from, date_to, org_id)
            if orders:
                print(f"First order revision: {orders[0].get('revision')}")
                print(f"Sample order keys: {list(orders[0].keys())}")
            else:
                print("No orders found in last 2 hours")
            
            await iiko_sync_service.sync_orders_by_revision(session, org_id)
            print("Finished call to sync_orders_by_revision")
        except Exception as e:
            print(f"Error in sync_orders_by_revision: {e}")

if __name__ == "__main__":
    asyncio.run(test())
