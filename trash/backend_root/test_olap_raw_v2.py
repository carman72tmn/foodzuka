import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

async def main():
    session = SessionLocal()
    settings = session.query(IikoSettings).first()
    
    base_url = settings.resto_url.rstrip('/')
    if not base_url.endswith('/resto'):
        base_url += '/resto'
        
    auth_url = f"{base_url}/api/auth?login={settings.resto_login}&pass={settings.resto_password}"
    print(f"Auth URL: {auth_url}")
    
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(auth_url)
        key = resp.text.strip()
        print(f"Auth key: {key}")
        
        # Try SALES report
        today = datetime.now().strftime("%Y-%m-%d")
        payload = {
            "reportType": "SALES",
            "groupByRowFields": [
                "OrderNum",
                "Courier.Name",
                "Delivery.Address",
                "Delivery.Region"
            ],
            "aggregateFields": [
                "fullSum"
            ],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": today,
                    "to": today
                },
                "OrderType": {
                    "filterType": "IncludeValues",
                    "values": ["Доставка"]
                }
            }
        }
        
        olap_url = f"{base_url}/api/v2/reports/olap?key={key}"
        print(f"OLAP URL: {olap_url}")
        resp = await client.post(olap_url, json=payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print("Error:", resp.text)
            return
            
        data = resp.json()
        rows = data.get("data", [])
        print(f"Fetched {len(rows)} rows from SALES report")
        if rows:
            print("First row:", rows[0])

if __name__ == "__main__":
    asyncio.run(main())
