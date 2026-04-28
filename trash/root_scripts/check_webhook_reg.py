import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def test():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        
        print(f"Checking webhooks for organization {settings.organization_id}...")
        # Iiko API has a method to get webhooks? 
        # Actually, we usually register them.
        # Let's check if there is an endpoint for that.
        
        # We can try to re-register just in case.
        # But first let's see if we have any info in the API.
        
        # Based on iiko docs, webhooks are managed via /api/1/webhooks/update_settings
        # We don't have a direct 'get' for settings in our service, but we can try to call it.
        pass

if __name__ == "__main__":
    asyncio.run(test())
