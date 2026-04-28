import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
import json
import httpx

async def test():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        
        # This ID is from our DB, it must exist in iiko if it was synced
        order_id = "f28264e7-783e-44e9-872e-9230473714d3"
        print(f"Fetching order {order_id} via /api/1/deliveries/by_id...")
        
        try:
            # We call the API directly to see the raw response
            token = await iiko_service._get_access_token(api_login=settings.api_login)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://api-ru.iiko.services/api/1/deliveries/by_id",
                    json={
                        "organizationId": settings.organization_id,
                        "orderIds": [order_id]
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
                print(f"Response Status: {response.status_code}")
                data = response.json()
                print("RAW RESPONSE:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
