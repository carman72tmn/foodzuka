import asyncio
import os
from app.core.database import SessionLocal
from app.services.iiko_service import IikoService
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
from datetime import datetime, timedelta
import json
import httpx

async def main():
    session = SessionLocal()
    query = select(IikoSettings)
    settings_db = session.exec(query).first()
    
    if not settings_db:
        print("No settings found")
        return
        
    iiko_service = IikoService()
    
    # Today only
    from_date = datetime.now().strftime("%Y-%m-%d 00:00:00.000")
    to_date = datetime.now().strftime("%Y-%m-%d 23:59:59.999")
    
    print(f"Fetching orders by delivery date from {from_date} to {to_date}...")
    
    token = await iiko_service._get_access_token(settings_db.api_login)
    
    payload = {
        "organizationIds": [settings_db.organization_id],
        "deliveryDateFrom": from_date,
        "deliveryDateTo": to_date
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{iiko_service.api_url}/api/1/deliveries/by_delivery_date_and_status",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=60.0
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # The structure for this endpoint is usually different from revision-based
            # Actually, the spec says it returns OrdersWithRevisionResponse (which has ordersByOrganizations)
            # OR sometimes it returns a simple list. Let's check.
            print("Response structure keys:", data.keys())
            
            orders_by_org = data.get('ordersByOrganizations', [])
            all_orders = []
            for org_data in orders_by_org:
                all_orders.extend(org_data.get('orders', []))
            
            # If not in ordersByOrganizations, check 'orders'
            if not all_orders:
                all_orders = data.get('orders', [])
                
            print(f"Found {len(all_orders)} orders total")
            
            if all_orders:
                print(f"Sample order ID: {all_orders[0].get('id')}")
                print("Address details for first order:")
                order = all_orders[0]
                dp = order.get('deliveryPoint', {})
                print(json.dumps(dp, indent=2, ensure_ascii=False))
                print(f"deliveryAddress: {order.get('deliveryAddress')}")
        else:
            print(f"Error response: {resp.text}")
    
    session.close()

if __name__ == "__main__":
    asyncio.run(main())
