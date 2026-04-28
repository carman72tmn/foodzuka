from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
import asyncio
import json

async def debug_restrictions():
    with SessionLocal() as db:
        s = db.query(IikoSettings).first()
        if not s:
            print("No settings")
            return
        
        print(f"Checking for org: {s.organization_id}")
        res = await iiko_service.get_delivery_restrictions(
            api_login=s.api_login,
            organization_id=s.organization_id
        )
        print("Raw result keys:", res.keys())
        print("Full raw result:", json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(debug_restrictions())
