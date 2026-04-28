import asyncio
import json
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.services.iiko_service import iiko_service
from app.models.iiko_settings import IikoSettings

async def inspect():
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        org_id = settings.organization_id
        
        now = datetime.utcnow()
        date_from = now - timedelta(hours=6)
        date_to = now + timedelta(hours=1)
        
        print(f"Fetching orders from {date_from} to {date_to}...")
        orders = await iiko_service.get_orders_by_date(date_from, date_to, organization_id=org_id)
        
        for o in orders:
            order_id = o.get("id")
            num = o.get("number")
            status = o.get("status")
            courier = o.get("courierInfo")
            print(f"Order #{num} (ID: {order_id}) - Status: {status} - Courier: {courier}")

if __name__ == "__main__":
    asyncio.run(inspect())
