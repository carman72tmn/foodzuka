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
    date_to = now + timedelta(hours=1) # Little bit into future just in case

    print(f"Checking Cloud orders from {date_from} to {date_to}")
    
    orders = await iiko_service.get_orders_by_date(
        date_from=date_from,
        date_to=date_to,
        organization_id=settings_db.organization_id,
        api_login=settings_db.api_login
    )
    
    print(f"Found {len(orders)} orders in Cloud")
    for o in orders[:5]:
        print(f" - ID: {o.get('id')}, Number: {o.get('number')}, Status: {o.get('status')}")

if __name__ == "__main__":
    asyncio.run(test())
