import asyncio
from datetime import datetime, timedelta
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
import pytz

async def test():
    db = SessionLocal()
    settings_db = db.query(IikoSettings).first()
    if not settings_db or not settings_db.organization_id:
        print("Iiko not configured")
        return

    tz = pytz.timezone(settings_db.timezone_name or "Asia/Yekaterinburg")
    now = datetime.now(tz)
    date_from = now - timedelta(hours=24)
    
    print(f"Checking ALL Cloud orders from {date_from}")
    
    # Прямой запрос к API через _request для отладки
    try:
        data = await iiko_service._request(
            "POST", 
            "/api/1/deliveries/by_delivery_date_and_status", 
            {
                "organizationIds": [settings_db.organization_id],
                "deliveryDateFrom": date_from.strftime("%Y-%m-%d %H:%M:%S.000")
            }
        )
        orders = data.get("orders", [])
        print(f"Found {len(orders)} orders in Cloud (without status filter)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
