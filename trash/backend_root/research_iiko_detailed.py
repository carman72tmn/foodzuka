import asyncio
import os
import json
from datetime import datetime, timedelta
from app.services.iiko_service import iiko_service
from app.core.config import settings

async def research_deliveries():
    print("Researching deliveries from iiko Cloud...")
    
    # Период: последние 3 дня
    date_to = datetime.now()
    date_from = date_to - timedelta(days=3)
    
    organization_id = settings.IIKO_ORGANIZATION_ID
    
    # 1. История доставок
    try:
        date_format = "%Y-%m-%d %H:%M:%S.000"
        payload = {
            "organizationIds": [organization_id],
            "deliveryDateFrom": date_from.strftime(date_format),
            "deliveryDateTo": date_to.strftime(date_format)
        }
        
        print(f"Requesting /api/1/deliveries/history for {organization_id} from {date_from} to {date_to}")
        data = await iiko_service._request("POST", "/api/1/deliveries/history", payload)
        
        with open("deliveries_history_sample.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(data.get('orders', []))} orders to deliveries_history_sample.json")
        
        if data.get('orders'):
            order = data['orders'][0]
            print("\nSample Order Fields:")
            print(f"Status: {order.get('status')}")
            print(f"Courier: {order.get('courierInfo', {}).get('courier', {}).get('name')}")
            print(f"Times: Created={order.get('whenCreated')}, CookingCompleted={order.get('whenCookingCompleted')}, Delivered={order.get('whenDelivered')}")
            
    except Exception as e:
        print(f"Error fetching history: {e}")

    # 2. Зоны доставки
    try:
        print("\nRequesting /api/1/delivery_restrictions...")
        zones_data = await iiko_service._request("GET", f"/api/1/delivery_restrictions?organizationIds={organization_id}")
        
        with open("delivery_restrictions_sample.json", "w", encoding="utf-8") as f:
            json.dump(zones_data, f, ensure_ascii=False, indent=2)
            
        print(f"Saved delivery restrictions to delivery_restrictions_sample.json")
    except Exception as e:
        print(f"Error fetching restrictions: {e}")

if __name__ == "__main__":
    asyncio.run(research_deliveries())
