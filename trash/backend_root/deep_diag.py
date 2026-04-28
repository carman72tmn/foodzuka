import asyncio
import httpx
import hashlib
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service

async def diag():
    print("--- DEEP DIAGNOSIS iiko RESTO OLAP ---")
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
            
        print(f"URL: {settings.resto_url}")
        print(f"Login: {settings.resto_login}")
        
        date_from = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = date_from
        
        try:
            print("Trying iiko_service.get_olap_report...")
            res = await iiko_service.get_olap_report(
                date_from=date_from,
                date_to=date_to,
                api_login=settings.api_login,
                organization_id=settings.organization_id,
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            print(f"SUCCESS! Rows: {len(res)}")
        except Exception as e:
            print(f"FAIL: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diag())
