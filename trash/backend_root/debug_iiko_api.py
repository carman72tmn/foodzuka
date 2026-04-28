import httpx
import json
from datetime import datetime, timedelta, timezone

login = '86dfd64bd15c42199b789edf6adcb289'
org_id = '2704eeae-dc5f-4c9f-9b81-375c454dd5bd'

async def debug():
    print(f"Testing Iiko API with login: {login[:4]}...")
    
    async with httpx.AsyncClient() as client:
        # 1. Get Token
        token_resp = await client.post('https://api-ru.iiko.services/api/1/access_token', json={'apiLogin': login})
        if token_resp.status_code != 200:
            print(f"Token error: {token_resp.text}")
            return
        
        token = token_resp.json().get('token')
        print(f"Token received: {token[:10]}...")
        
        # 2. Get Organizations
        orgs_resp = await client.get('https://api-ru.iiko.services/api/1/organizations', headers={'Authorization': f'Bearer {token}'})
        orgs = orgs_resp.json().get('organizations', [])
        print(f"Found {len(orgs)} organizations:")
        for o in orgs:
            print(f" - {o.get('name')} (ID: {o.get('id')})")
        
        # 3. Check if target ORG exists
        target_org = next((o for o in orgs if o.get('id') == org_id), None)
        if not target_org:
            print(f"WARNING: Target Organization ID {org_id} NOT FOUND in your account!")
        else:
            print(f"Target organization found: {target_org.get('name')}")
        
        # 4. Try to fetch orders for today (April 21)
        date_from = "2026-04-21 18:00:00.000"
        date_to = "2026-04-21 19:00:00.000"
        
        print(f"Fetching orders from {date_from} to {date_to}...")
        
        orders_payload = {
            "organizationIds": [org_id],
            "deliveryDateFrom": date_from,
            "deliveryDateTo": date_to
        }
        
        orders_resp = await client.post('https://api-ru.iiko.services/api/1/deliveries/by_delivery_date_and_status', json=orders_payload, headers={'Authorization': f'Bearer {token}'})
        
        if orders_resp.status_code == 200:
            orders = orders_resp.json().get('orders', [])
            print(f"Successfully fetched {len(orders)} orders.")
            if orders:
                print(f"Latest order: {orders[0].get('id')} - {orders[0].get('externalNumber')} - {orders[0].get('status')}")
        else:
            print(f"Orders fetch error {orders_resp.status_code}: {orders_resp.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug())
