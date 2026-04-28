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
        
        statuses = [
            "Unconfirmed", "WaitCooking", "ReadyForCooking", "CookingStarted", 
            "CookingCompleted", "Waiting", "OnWay", "Delivered", "Closed", "Cancelled"
        ]
        
        print(f"Fetching orders with statuses from {date_from} to {date_to}...")
        
        # We can't use get_orders_by_date directly because it doesn't take statuses as argument 
        # (it's hardcoded to None in the call to _request)
        # Wait, let's check get_orders_by_date definition again.
        
        org_id = settings.organization_id
        data = await iiko_service._request(
            "POST", 
            "/api/1/deliveries/by_delivery_date_and_status", 
            {
                "organizationIds": [org_id],
                "deliveryDateFrom": date_from.strftime("%Y-%m-%d %H:%M:%S.000"),
                "deliveryDateTo": date_to.strftime("%Y-%m-%d %H:%M:%S.000"),
                "statuses": statuses
            },
            api_login=settings.api_login,
            organization_id=org_id
        )
        
        orders = data.get("ordersByOrganizations", [])
        print(f"Found {len(orders)} organization blocks")
        for org_block in orders:
            org_orders = org_block.get("orders", [])
            print(f"Org {org_block.get('organizationId')} has {len(org_orders)} orders")
            for o in org_orders[:10]:
                print(f"Num: {o.get('number')} | Status: {o.get('status')} | ID: {o.get('id')}")

if __name__ == "__main__":
    asyncio.run(test())
