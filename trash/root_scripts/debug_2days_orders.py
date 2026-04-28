import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
from datetime import datetime, timedelta

async def test():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        
        now = datetime.now()
        date_from = now - timedelta(days=2)
        date_to = now + timedelta(days=1)
        
        print(f"Fetching orders from {date_from} to {date_to} for organization {settings.organization_id}...")
        orders = await iiko_service.get_orders_by_date(
            date_from=date_from,
            date_to=date_to,
            organization_id=settings.organization_id,
            api_login=settings.api_login
        )
        print(f"Found {len(orders)} orders")
        if orders:
            for o in orders[:10]:
                order_data = o.get("order", {})
                print(f"Num: {order_data.get('number')} | Status: {order_data.get('status')} | ID: {o.get('id')}")

if __name__ == "__main__":
    asyncio.run(test())
