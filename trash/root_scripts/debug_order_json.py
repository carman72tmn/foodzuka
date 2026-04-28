import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
from datetime import datetime, timedelta
import json

async def test():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        
        now = datetime.now()
        date_from = now - timedelta(hours=48)
        date_to = now + timedelta(hours=24)
        
        print(f"Fetching orders for the last 48h...")
        
        org_id = settings.organization_id
        data = await iiko_service._request(
            "POST", 
            "/api/1/deliveries/by_delivery_date_and_status", 
            {
                "organizationIds": [org_id],
                "deliveryDateFrom": date_from.strftime("%Y-%m-%d %H:%M:%S.000"),
                "deliveryDateTo": date_to.strftime("%Y-%m-%d %H:%M:%S.000"),
                "statuses": ["Closed", "Delivered", "OnWay", "Waiting"]
            },
            api_login=settings.api_login,
            organization_id=org_id
        )
        
        orgs_data = data.get("ordersByOrganizations", [])
        if not orgs_data:
            print("No ordersByOrganizations found")
            return
            
        for org_block in orgs_data:
            orders = org_block.get("orders", [])
            print(f"Found {len(orders)} orders for org {org_block.get('organizationId')}")
            for o in orders[:1]:
                print("SAMPLE ORDER JSON:")
                print(json.dumps(o, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test())
