import asyncio
import httpx
import hashlib
from app.services.iiko_service import iiko_service

async def main():
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    db_settings = await iiko_service._get_settings_by_org_id(org_id)
    base_url = "https://dovezzuka-tyumen.iiko.it/resto/api"
    
    login = db_settings.resto_login
    password = db_settings.resto_password
    password_sha1 = hashlib.sha1(password.encode()).hexdigest()
    
    async with httpx.AsyncClient(verify=False) as client:
        auth_resp = await client.get(f"{base_url}/auth", params={"login": login, "pass": password_sha1})
        token = auth_resp.text.strip().replace('"', '')
        
        phone = "79000000000"
        field = "Delivery.CustomerPhone"
        
        # Попробуем разные наборы агрегатов
        aggregates = [
            ["DishDiscountSumInt", "fullSum", "DiscountSum", "UniqOrderId", "DishAmountInt"],
            ["DishDiscountSum", "fullSum", "DiscountSum", "UniqOrderId", "DishAmount"],
            ["fullSum", "DiscountSum", "UniqOrderId"]
        ]
        
        for aggr in aggregates:
            print(f"\n--- Testing aggregates: {aggr} ---")
            payload = {
                "reportType": "SALES",
                "groupByRowFields": [field],
                "aggregateFields": aggr,
                "filters": {
                    "OpenDate.Typed": {
                        "filterType": "DateRange",
                        "from": "2021-01-01",
                        "to": "2026-12-31",
                        "includeLow": True,
                        "includeHigh": True
                    },
                    field: {
                        "filterType": "IncludeValues",
                        "values": [phone]
                    }
                }
            }
            resp = await client.post(f"{base_url}/v2/reports/olap?key={token}", json=payload)
            print(f"Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"Response: {resp.text}")
            else:
                print("SUCCESS!")

if __name__ == "__main__":
    asyncio.run(main())
