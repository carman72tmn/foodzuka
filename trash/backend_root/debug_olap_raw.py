import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

async def main():
    session = SessionLocal()
    settings = session.query(IikoSettings).first()
    if not settings:
        print("No settings found")
        return

    # Тюмень UTC+5
    tz = timezone(timedelta(hours=5))
    now = datetime.now(tz)
    date_from = now - timedelta(days=2) # 2 days ago
    date_to = now + timedelta(days=1)
    
    print(f"Fetching OLAP SALES report from {date_from} to {date_to}...")
    
    # Try SALES instead of DELIVERIES
    v2_from = date_from.strftime("%Y-%m-%d")
    v2_to = date_to.strftime("%Y-%m-%d")
    
    payload = {
        "reportType": "SALES",
        "groupByRowFields": [
            "OrderNum",
            "Courier.Name",
            "Delivery.Address",
            "Delivery.ActualTime",
            "Delivery.ExpectedTime"
        ],
        "aggregateFields": [
            "fullSum"
        ],
        "filters": {
            "OpenDate.Typed": {
                "filterType": "DateRange",
                "periodType": "CUSTOM",
                "from": v2_from,
                "to": v2_to
            },
            "OrderType": {
                "filterType": "IncludeValues",
                "values": ["Доставка"] # Only deliveries
            }
        }
    }
    
    # We need to manually call the request since get_resto_detailed_deliveries is hardcoded to DELIVERIES
    # But wait, iiko_service has a method for raw requests? No.
    # I'll just temporarily modify iiko_service.py to use SALES and see if it works.
    
    deliveries = await iiko_service.get_resto_detailed_deliveries(
        date_from=date_from,
        date_to=date_to,
        organization_id=settings.organization_id
    )
    
    print(f"Fetched {len(deliveries)} deliveries")
    if deliveries:
        print("First delivery raw:", deliveries[0])

if __name__ == "__main__":
    asyncio.run(main())
