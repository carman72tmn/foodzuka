import asyncio
from datetime import datetime
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service

async def main():
    with Session(engine) as s:
        db = s.exec(select(IikoSettings)).first()
        if not db:
            print("No settings!")
            return
        
        print(f"URL: {db.resto_url}, Login: {db.resto_login}")
        
        # Test attendance endpoint
        try:
            result = await iiko_service.get_resto_attendance(
                db.resto_url, db.resto_login, db.resto_password,
                datetime(2026, 4, 11), datetime(2026, 4, 18)
            )
            print(f"Attendance rows: {len(result)}")
            for r in result[:3]:
                print(f"  {r}")
        except Exception as e:
            print(f"attendance ERROR: {e}")

asyncio.run(main())
