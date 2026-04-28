import asyncio
import hashlib
import httpx
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings

async def test_delivery_details():
    with Session(engine) as session:
        s = session.exec(select(IikoSettings)).first()
        url, login, password = s.resto_url, s.resto_login, s.resto_password
        
    base_url = "https://dovezzuka-tyumen.iiko.it/resto/api"
    pwd_hash = hashlib.sha1(password.encode()).hexdigest()
    
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        token = r.text.strip().strip('"')
        
        payload = {
            "reportType": "DELIVERIES",
            "groupByRowFields": [
                "OrderNum", 
                "Delivery.Street", 
                "Delivery.ActualTime", 
                "Delivery.ExpectedTime",
                "Delivery.Zone",
                "WaiterName"
            ],
            "aggregateFields": ["DishDiscountSumInt"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": "2026-04-15T00:00:00.000",
                    "to": "2026-04-19T00:00:00.000",
                    "includeLow": True,
                    "includeHigh": False
                }
            }
        }
        
        r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
        if r2.status_code == 200:
            data = r2.json()
            print(f"DELIVERIES rows: {len(data.get('data', []))}")
            for row in data.get('data', [])[:10]:
                print(f"  {row}")
        else:
            print(f"Error: {r2.text}")

if __name__ == "__main__":
    asyncio.run(test_delivery_details())
