import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
import time

async def test():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        
        org_id = settings.organization_id
        api_login = settings.api_login
        
        for i in range(5):
            data = await iiko_service._request(
                "POST", 
                "/api/1/deliveries/by_delivery_date_and_status", 
                {
                    "organizationIds": [org_id],
                    "deliveryDateFrom": "2026-04-22 00:00:00.000",
                    "deliveryDateTo": "2026-04-23 23:59:59.000"
                },
                api_login=api_login,
                organization_id=org_id
            )
            print(f"Iter {i}: MaxRev: {data.get('maxRevision')}")
            time.sleep(5)

if __name__ == "__main__":
    asyncio.run(test())
