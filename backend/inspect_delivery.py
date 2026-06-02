import asyncio
import logging
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from sqlmodel import select
from app.models.iiko_settings import IikoSettings
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

async def inspect_delivery():
    session = SessionLocal()
    settings_db = session.exec(select(IikoSettings)).first()
    
    date_to = datetime.now()
    date_from = date_to - timedelta(days=1)
    
    # Try with a very simple report first
    print("Fetching one delivery with basic fields...")
    deliveries = await iiko_service.get_resto_detailed_deliveries(
        date_from=date_from,
        date_to=date_to,
        organization_id=settings_db.organization_id
    )
    
    if deliveries:
        print("First delivery keys:")
        print(deliveries[0].keys())
        print("First delivery data:")
        print(deliveries[0])
    else:
        print("No deliveries found.")

if __name__ == "__main__":
    asyncio.run(inspect_delivery())
