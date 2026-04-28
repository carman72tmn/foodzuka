import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service

async def test_iiko_sync():
    with Session(engine) as session:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db:
            print("Settings not found")
            return
        
        org_id = settings_db.organization_id
        print(f"Testing for Org: {org_id}")
        
        # Today's range
        now = datetime.now()
        date_from = now - timedelta(hours=12)
        date_to = now + timedelta(hours=12)
        
        print(f"Requesting range: {date_from} to {date_to}")
        
        try:
            orders = await iiko_service.get_orders_by_date(
                date_from=date_from,
                date_to=date_to,
                organization_id=org_id,
                api_login=settings_db.api_login
            )
            print(f"Successfully fetched {len(orders)} orders")
            if orders:
                for o in orders[:3]:
                    print(f"Order: ID={o.get('id')}, Num={o.get('number')}, Status={o.get('status')}")
            else:
                print("No orders found in this range.")
                
        except Exception as e:
            print(f"Error during API call: {e}")

if __name__ == "__main__":
    asyncio.run(test_iiko_sync())
