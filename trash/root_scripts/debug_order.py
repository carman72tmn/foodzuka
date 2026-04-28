import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
import json

async def test():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        
        order_id = "f28264e7-783e-44e9-872e-9230473714d3"
        print(f"Fetching order {order_id}...")
        
        order_data = await iiko_service.get_order_by_id(
            order_id, 
            settings.organization_id, 
            api_login=settings.api_login
        )
        
        if not order_data:
            print("Order not found")
            return
            
        print("ORDER DATA:")
        # Print with indent to see the structure
        print(json.dumps(order_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test())
