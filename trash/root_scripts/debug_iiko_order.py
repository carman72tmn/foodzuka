import asyncio
import json
from app.services.iiko_service import iiko_service

async def check_order():
    order_id = "17e5ac36-1cc1-4654-9de8-eaad7cd4709f"
    # Нам нужен organization_id, возьмем из конфига iiko_service
    org_id = iiko_service.organization_id
    
    print(f"Fetching order {order_id} for org {org_id}")
    order_data = await iiko_service.get_order_by_id(order_id, org_id)
    
    if order_data:
        print(json.dumps(order_data, indent=2, ensure_ascii=False))
    else:
        print("Order not found in Iiko Cloud")

if __name__ == "__main__":
    asyncio.run(check_order())
