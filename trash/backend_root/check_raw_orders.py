import asyncio
import os
import sys
from datetime import datetime, timedelta

# Добавляем путь к приложению
sys.path.append("/app")
from app.services.iiko_service import iiko_service

async def check_raw_orders():
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    now = datetime.now()
    dt_from = now - timedelta(hours=2)
    dt_to = now + timedelta(hours=1)
    
    date_format = "%Y-%m-%d %H:%M:%S.000"
    payload = {
        "organizationIds": [org_id],
        "deliveryDateFrom": dt_from.strftime(date_format),
        "deliveryDateTo": dt_to.strftime(date_format)
    }
    
    print(f"Requesting raw orders...")
    try:
        data = await iiko_service._request(
            "POST", "/api/1/deliveries/by_delivery_date_and_status", 
            payload,
            organization_id=org_id
        )
        orders = data.get("orders", [])
        print(f"Found {len(orders)} orders.")
        if orders:
            print(f"Keys in first order: {orders[0].keys()}")
            print(f"Revision of first order: {orders[0].get('revision')}")
            # print(f"Sample order: {orders[0]}")
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    asyncio.run(check_raw_orders())
