import asyncio
import json
from app.services.iiko_service import iiko_service
from app.core.database import engine
from sqlmodel import Session, select
from app.models import IikoSettings

async def test_orgs():
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return

        api_login = settings.api_login
        
        print(f"Fetching organizations for api_login...")
        try:
            orgs = await iiko_service.get_organizations(api_login=api_login)
            print(f"Found {len(orgs)} organizations:")
            for o in orgs:
                print(f"ID: {o.get('id')} | Name: {o.get('name')}")
        except Exception as e:
            print(f"Error fetching orgs: {e}")

if __name__ == "__main__":
    asyncio.run(test_orgs())
