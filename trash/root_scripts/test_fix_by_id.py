import asyncio
import json
from app.services.iiko_service import IikoService
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

async def main():
    service = IikoService()
    db = SessionLocal()
    settings = db.query(IikoSettings).first()
    db.close()
    
    org_id = settings.organization_id
    order_id = "17e5ac36-1cc1-4654-9de8-eaad7cd4709f"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    print(f"Testing service.get_order_by_id for order {order_id}...")
    order = await service.get_order_by_id(order_id, org_id)
    
    if order:
        print("Successfully retrieved order!")
        print(json.dumps(order, indent=2, ensure_ascii=False))
    else:
        print("Order not found or error occurred.")

if __name__ == "__main__":
    asyncio.run(main())
