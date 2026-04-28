import asyncio
import os
from app.core.database import SessionLocal
from app.services.iiko_service import IikoService
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
import json

async def main():
    session = SessionLocal()
    query = select(IikoSettings)
    settings_db = session.exec(query).first()
    
    if not settings_db:
        print("No settings found")
        return
        
    iiko_service = IikoService()
    print("Fetching all organizations...")
    orgs = await iiko_service.get_organizations(settings_db.api_login)
    print(json.dumps(orgs, indent=2, ensure_ascii=False))
    
    session.close()

if __name__ == "__main__":
    asyncio.run(main())
