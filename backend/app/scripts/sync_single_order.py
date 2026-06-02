import asyncio
import os
import sys
import logging
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import iiko_sync_service
from app.services.iiko_service import iiko_service

logging.basicConfig(level=logging.INFO)

async def sync_order(order_iiko_id: str):
    print(f"Starting manual sync for order {order_iiko_id}...")
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Error: Iiko settings not found.")
            return

        try:
            # Запрашиваем заказ по ID
            # Эндпоинт: /api/1/deliveries/by_id
            print(f"Fetching order {order_iiko_id} from iiko...")
            data = await iiko_service._request(
                "POST", "/api/1/deliveries/by_id",
                {
                    "organizationId": settings.organization_id,
                    "orderIds": [order_iiko_id]
                },
                api_login=settings.api_login,
                organization_id=settings.organization_id
            )
            
            # В Iiko Cloud API v2 заказы обычно в ordersByOrganizations
            orders = data.get("orders", [])
            if not orders:
                organizations_data = data.get("ordersByOrganizations", [])
                for org_data in organizations_data:
                    orders.extend(org_data.get("orders", []))
            
            if not orders:
                print(f"Order {order_iiko_id} not found in iiko response.")
                print(f"Response: {data}")
                return
            
            order_data = orders[0]
            # В iiko Cloud API v2 ответ от by_id содержит структуру с 'order' внутри
            real_order_data = order_data.get('order') or order_data
            raw_status = real_order_data.get('status') or order_data.get('creationStatus')
            
            print(f"DEBUG: raw_status from iiko: '{raw_status}'")
            print(f"Found order in iiko. Status: {raw_status}, Type: {real_order_data.get('orderTypeId')}")
            
            await iiko_sync_service.process_iiko_order(
                session, 
                order_data, 
                settings.organization_id
            )
            print(f"Sync completed successfully for order {order_iiko_id}.")
            
        except Exception as e:
            print(f"Error during sync: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sync_single_order.py <iiko_order_id>")
        sys.exit(1)
    
    order_id = sys.argv[1]
    asyncio.run(sync_order(order_id))
