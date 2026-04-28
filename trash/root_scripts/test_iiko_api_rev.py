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
        
        # Get actual current max
        max_rev = await iiko_service.get_max_revision(settings.organization_id, settings.api_login)
        print(f"Current Max Rev: {max_rev}")
        
        rev = max_rev - 10
        print(f"Testing for Org: {settings.organization_id}, Trying Rev: {rev}")
        
        response = await iiko_service.get_deliveries_by_revision(
            organization_id=settings.organization_id,
            initial_revision=rev,
            api_login=settings.api_login
        )
        
        orders = response.get("orders", [])
        print(f"Found {len(orders)} orders via get_deliveries_by_revision")
        if orders:
            orders.sort(key=lambda x: x.get('revision', 0), reverse=True)
            print(f"Sample order 0: {orders[0].get('number')} - {orders[0].get('status')} (Rev: {orders[0].get('revision')})")
            o = orders[0].get('order') or orders[0]
            print(f"Address top: {o.get('address')}")
            print(f"DeliveryPoint: {o.get('deliveryPoint')}")

if __name__ == "__main__":
    asyncio.run(test())
