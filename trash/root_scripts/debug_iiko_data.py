import asyncio
import httpx
import sys
import json
from datetime import datetime, timedelta

async def main():
    api_url = 'https://api-ru.iiko.services'
    login = '86dfd64bd15c42199b789edf6adcb289'
    org_id = '2704eeae-dc5f-4c9f-9b81-375c454dd5bd'
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Auth
        resp = await client.post(f'{api_url}/api/1/access_token', json={'apiLogin': login})
        token = resp.json().get('token')
        
        # Yesterday
        df = "2026-04-22 00:00:00.000"
        dt = "2026-04-22 23:59:59.000"
        
        payload = {
            "organizationIds": [org_id],
            "deliveryDateFrom": df,
            "deliveryDateTo": dt
        }
        print(f"Requesting for YESTERDAY {df} - {dt}...")
        resp = await client.post(f'{api_url}/api/1/deliveries/by_delivery_date_and_status', 
                                headers={'Authorization': f'Bearer {token}'},
                                json=payload)
        print(f"Full Response: {resp.text}")

if __name__ == '__main__':
    asyncio.run(main())
