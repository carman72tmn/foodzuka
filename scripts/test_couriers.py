import asyncio
import json
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def main():
    with SessionLocal() as session:
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login
        org_id = settings_db.organization_id
        
        print(f"Fetching couriers for org {org_id}...")
        
        # Запрашиваем список курьеров
        res = await iiko_service._request(
            "POST", "/api/1/employees/couriers",
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        
        print("COURIERS RESPONSE:")
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
