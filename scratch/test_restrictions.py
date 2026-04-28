import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

async def test():
    db = SessionLocal()
    settings_db = db.query(IikoSettings).first()
    if not settings_db or not settings_db.organization_id:
        print("Iiko not configured")
        return

    print(f"Checking delivery restrictions for org: {settings_db.organization_id}")
    
    data = await iiko_service.get_delivery_restrictions(
        api_login=settings_db.api_login,
        organization_id=settings_db.organization_id
    )
    
    print(f"Type: {type(data)}")
    print(f"Data: {data}")

if __name__ == "__main__":
    asyncio.run(test())
