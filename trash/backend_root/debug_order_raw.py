import asyncio
import os
import sys
import json

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def main():
    order_id = "93af37bb-0e74-4e2c-9a21-51a554c17c72" # Order 358
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        org_id = settings.organization_id
        api_login = settings.api_login
        
        print(f"Fetching raw data for order {order_id}...")
        order_data = await iiko_service.get_order_by_id(order_id, org_id, api_login=api_login)
        
        if order_data:
            print(json.dumps(order_data, indent=2, ensure_ascii=False))
        else:
            print("Order not found in iiko Cloud.")

if __name__ == "__main__":
    asyncio.run(main())
