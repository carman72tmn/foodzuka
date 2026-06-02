import asyncio
import logging
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from sqlmodel import select
from app.models.iiko_settings import IikoSettings

logging.basicConfig(level=logging.INFO)

async def check_columns():
    session = SessionLocal()
    settings_db = session.exec(select(IikoSettings)).first()
    if not settings_db:
        print("Settings not found")
        return
        
    print("Fetching OLAP columns for DELIVERIES report...")
    columns = await iiko_service.get_resto_olap_columns(
        report_type="DELIVERIES",
        organization_id=settings_db.organization_id
    )
    
    print(f"Fetched {len(columns)} columns.")
    for col in columns:
        name = col.get("name")
        if "Courier" in name or "Driver" in name:
            print(f"  Column: {name}")

if __name__ == "__main__":
    asyncio.run(check_columns())
