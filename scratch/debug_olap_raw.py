import asyncio
from app.core.database import engine
from app.services.iiko_service import iiko_service
from app.models.iiko_settings import IikoSettings
from sqlmodel import Session, select
from datetime import datetime, timedelta
import json

async def debug_raw_olap():
    print("Fetching raw OLAP response...")
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        
        date_from = datetime.now() - timedelta(days=5)
        date_to = datetime.now()
        
        v2_from = date_from.strftime("%Y-%m-%d")
        v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%d")
        
        payload = {
            "reportType": "DELIVERIES",
            "groupByRowFields": [
                "Delivery.Number", 
                "Delivery.Courier", 
                "Delivery.ActualTime"
            ],
            "aggregateFields": [
                "fullSum"
            ],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": v2_from,
                    "to": v2_to,
                    "includeLow": True,
                    "includeHigh": True
                }
            }
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = await iiko_service._resto_request(
                "POST", "/v2/reports/olap",
                json_data=payload,
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            print("Raw Response Keys:", response.keys() if isinstance(response, dict) else "Not a dict")
            print("Data length:", len(response.get("data", [])) if isinstance(response, dict) else "N/A")
            if isinstance(response, dict) and response.get("data"):
                print("First 2 rows:", response.get("data")[:2])
            else:
                print("Response:", response)
                
            # Try SALES report as fallback test
            print("\nTesting SALES report...")
            payload["reportType"] = "SALES"
            response_sales = await iiko_service._resto_request(
                "POST", "/v2/reports/olap",
                json_data=payload,
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            print("SALES Data length:", len(response_sales.get("data", [])) if isinstance(response_sales, dict) else "N/A")
            
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_raw_olap())
