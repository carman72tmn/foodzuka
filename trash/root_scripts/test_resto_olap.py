import asyncio
import hashlib
import httpx
import json
from datetime import datetime, timedelta

RESTO_URL = "https://dovezzuka-tyumen.iiko.it/resto"
RESTO_LOGIN = "superapi"
RESTO_PASS = "7r6zp53q"

async def test_resto():
    base_url = RESTO_URL.rstrip('/') + "/api"
    auth_url = f"{base_url}/auth"
    
    password_sha1 = hashlib.sha1(RESTO_PASS.encode()).hexdigest()
    
    async with httpx.AsyncClient(verify=False) as client:
        print(f"Testing auth at {auth_url}...")
        resp = await client.get(auth_url, params={"login": RESTO_LOGIN, "pass": password_sha1})
        
        if resp.status_code != 200:
            print(f"Auth failed: {resp.status_code} {resp.text}")
            return
        
        token = resp.text.strip().replace('"', '')
        print(f"Auth success, token: {token}")
        
        # Test SALES report
        print("\nTesting SALES report (v2)...")
        olap_url = f"{base_url}/v2/reports/olap"
        payload = {
            "reportType": "SALES",
            "groupByRowFields": ["Department", "OpenDate.Typed"],
            "aggregateFields": [
            "OrderSum", 
            "DiscountSum", 
            "GuestNum", 
            "DishAmountInt",
            "ProductCostBase.ProductCost",
            "ProductCostBase.MarkUp",
            "ProductCostBase.Profit",
            "ProductCostBase.Percent"
        ],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000"),
                    "to": datetime.now().strftime("%Y-%m-%dT00:00:00.000"),
                    "includeLow": True,
                    "includeHigh": False
                }
            }
        }
        
        resp = await client.post(olap_url, params={"key": token}, json=payload)
        print(f"SALES v2 Status: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"SALES v2 Response keys: {list(data.keys())}")
                if data.get('data'):
                    print(f"SALES v2 First row: {data['data'][0]}")
                    print(f"SALES v2 Column names: {data.get('columnNames')}")
            except:
                print(f"SALES v2 Response is not JSON. Starts with: {resp.text[:100]}")
        else:
            print(f"SALES v2 Failed: {resp.text[:200]}")

        # Test DELIVERIES report
        print("\nTesting DELIVERIES report (v2)...")
        payload["reportType"] = "DELIVERIES"
        payload["groupByRowFields"] = ["Delivery.Number", "Delivery.Courier"]
        payload["aggregateFields"] = ["fullSum"]
        
        resp = await client.post(olap_url, params={"key": token}, json=payload)
        print(f"DELIVERIES v2 Status: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"DELIVERIES v2 Data keys: {list(data.keys())}")
                print(f"Rows count: {len(data.get('data', []))}")
            except:
                print(f"DELIVERIES v2 Response is not JSON. Starts with: {resp.text[:100]}")
        else:
            print(f"DELIVERIES v2 Failed: {resp.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_resto())
