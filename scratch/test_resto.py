import asyncio
from datetime import datetime, timedelta
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

async def test():
    db = SessionLocal()
    settings_db = db.query(IikoSettings).first()
    if not settings_db or not settings_db.resto_url:
        print("Resto not configured")
        return

    now = datetime.now()
    date_from = now - timedelta(days=1)
    date_to = now + timedelta(days=1)

    print(f"Checking Resto from {date_from} to {date_to}")
    
    ids = await iiko_service.get_resto_delivery_history(
        date_from=date_from,
        date_to=date_to,
        resto_url=settings_db.resto_url,
        resto_login=settings_db.resto_login,
        resto_password=settings_db.resto_password
    )
    
    print(f"Found {len(ids)} orders in Resto")
    for oid in ids[:10]:
        print(f" - {oid}")

if __name__ == "__main__":
    asyncio.run(test())
