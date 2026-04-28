import httpx
import json
import asyncio
from datetime import datetime, timedelta

login = '86dfd64bd15c42199b789edf6adcb289'
org_id = '2704eeae-dc5f-4c9f-9b81-375c454dd5bd'

async def debug():
    async with httpx.AsyncClient() as client:
        token_resp = await client.post('https://api-ru.iiko.services/api/1/access_token', json={'apiLogin': login})
        token = token_resp.json().get('token')
        
        # Wide range: last 2 days
        date_format = "%Y-%m-%d %H:%M:%S.000"
        now = datetime.now()
        date_from = (now - timedelta(days=2)).strftime(date_format)
        date_to = (now + timedelta(days=1)).strftime(date_format)
        
        print(f"Fetching delivery history from {date_from} to {date_to}...")
        payload = {
            "organizationIds": [org_id],
            "deliveryDateFrom": date_from,
            "deliveryDateTo": date_to
        }
        
        # Try history endpoint
        resp = await client.post('https://api-ru.iiko.services/api/1/deliveries/history', json=payload, headers={'Authorization': f'Bearer {token}'})
        
        if resp.status_code == 200:
            orders = resp.json().get('orders', [])
            print(f"Found {len(orders)} orders in history.")
            for o in orders[:10]:
                print(f" - {o.get('externalNumber')} | Status: {o.get('status')} | Date: {o.get('deliveryDate')}")
        else:
            print(f"History Error {resp.status_code}: {resp.text}")
            
        # Try by_delivery_date_and_status endpoint
        print("\nTrying by_delivery_date_and_status...")
        payload["statuses"] = ["Unconfirmed", "WaitCooking", "ReadyForCooking", "CookingStarted", "CookingCompleted", "Waiting", "OnWay", "Delivered", "Closed", "Cancelled"]
        resp = await client.post('https://api-ru.iiko.services/api/1/deliveries/by_delivery_date_and_status', json=payload, headers={'Authorization': f'Bearer {token}'})
        
        if resp.status_code == 200:
            orders = resp.json().get('orders', [])
            print(f"Found {len(orders)} orders in by_delivery_date_and_status.")
            for o in orders[:10]:
                print(f" - {o.get('externalNumber')} | Status: {o.get('status')} | Date: {o.get('deliveryDate')}")
        else:
            print(f"ByDate Error {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    asyncio.run(debug())
