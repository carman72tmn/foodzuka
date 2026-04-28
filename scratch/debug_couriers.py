import asyncio
from app.core.database import engine
from app.services.iiko_service import iiko_service
from app.models.iiko_settings import IikoSettings
from sqlmodel import Session, select
from datetime import datetime, timedelta
import json

async def debug_courier_names():
    print("Checking unique courier names in OLAP...")
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        
        date_from = datetime.now() - timedelta(days=5)
        date_to = datetime.now()
        
        payload = {
            "reportType": "DELIVERIES",
            "groupByRowFields": ["Delivery.Courier"],
            "aggregateFields": ["fullSum"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": date_from.strftime("%Y-%m-%d"),
                    "to": (date_to + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "includeLow": True, "includeHigh": True
                }
            }
        }
        
        try:
            response = await iiko_service._resto_request(
                "POST", "/v2/reports/olap",
                json_data=payload,
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            data = response.get("data", [])
            couriers = set()
            for row in data:
                couriers.add(row.get("Delivery.Courier"))
            print("Unique couriers found:", couriers)
            print("Total rows:", len(data))
            
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_courier_names())
