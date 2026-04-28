import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def test():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        
        print(f"Fetching active orders for organization {settings.organization_id}...")
        orders = await iiko_service.get_active_orders(
            organization_id=settings.organization_id,
            api_login=settings.api_login
        )
        print(f"Found {len(orders)} active orders")
        for o in orders:
            order_data = o.get("order", {})
            print(f"Num: {order_data.get('number')} | Status: {order_data.get('status')} | ID: {o.get('id')}")

if __name__ == "__main__":
    asyncio.run(test())
