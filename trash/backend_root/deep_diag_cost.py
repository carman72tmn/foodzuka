import asyncio
import httpx
import hashlib
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings

async def test_resto():
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        
    password_sha1 = hashlib.sha1(settings.resto_password.encode()).hexdigest()
    base_url = settings.resto_url.rstrip('/') + "/api"
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        auth = await client.get(f"{base_url}/auth", params={"login": settings.resto_login, "pass": password_sha1})
        token = auth.text.strip().replace('"', '')
        print("Token:", token[:10])
        
        date_from = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = date_from
        v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
        v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
        
        payload = {
            "reportType": "SALES",
            "groupByRowFields": ["Department", "OpenDate.Typed"],
            "aggregateFields": [
                "DishDiscountSumInt", 
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
                    "from": v2_from,
                    "to": v2_to,
                    "includeLow": True,
                    "includeHigh": False
                },
                "OrderDeleted": {
                    "filterType": "IncludeValues",
                    "values": ["NOT_DELETED"]
                }
            }
        }
        
        print("Sending payload:", payload)
        resp = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
        print(f"Status: {resp.status_code}")
        print("Response:", resp.text[:1000])

if __name__ == "__main__":
    asyncio.run(test_resto())
