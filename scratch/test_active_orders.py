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

    print(f"Checking Active orders (by revision) for org: {settings_db.organization_id}")
    
    orders = await iiko_service.get_active_orders(
        organization_id=settings_db.organization_id,
        api_login=settings_db.api_login
    )
    
    print(f"Found {len(orders)} active orders")
    for o in orders[:5]:
        print(f" - ID: {o.get('id')}, Number: {o.get('number')}, Status: {o.get('status')}")

if __name__ == "__main__":
    asyncio.run(test())
