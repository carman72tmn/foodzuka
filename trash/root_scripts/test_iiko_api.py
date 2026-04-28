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
        
        print(f"Testing for Org: {settings.organization_id}")
        
        # Test 1: get_orders_by_date for last 24h
        now = datetime.now()
        date_from = now - timedelta(hours=24)
        date_to = now + timedelta(hours=2)
        
        print(f"Requesting orders from {date_from} to {date_to}")
        orders = await iiko_service.get_orders_by_date(
            organization_id=settings.organization_id,
            date_from=date_from,
            date_to=date_to,
            api_login=settings.api_login
        )
        
        print(f"Found {len(orders)} orders via get_orders_by_date")
        if orders:
            print(f"Sample order 0: {orders[0].get('number')} - {orders[0].get('status')}")
            # Check address structure
            o = orders[0]
            print(f"Address top: {o.get('address')}")
            print(f"DeliveryPoint: {o.get('deliveryPoint')}")

if __name__ == "__main__":
    asyncio.run(test())
