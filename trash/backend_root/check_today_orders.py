import asyncio
import os
import sys
from datetime import datetime, timedelta

# Добавляем путь к приложению
sys.path.append("/app")
from app.services.iiko_service import iiko_service

async def check_today_orders():
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    now = datetime.now()
    dt_from = now - timedelta(hours=24)
    dt_to = now + timedelta(hours=1)
    
    print(f"Fetching orders from {dt_from} to {dt_to}...")
    try:
        orders = await iiko_service.get_orders_by_date(dt_from, dt_to, organization_id=org_id)
        print(f"SUCCESS! Found {len(orders)} orders.")
        if orders:
            revisions = [o.get("revision", 0) for o in orders]
            print(f"Revisions: {revisions}")
            print(f"Max Revision: {max(revisions)}")
            print(f"First order sample: {orders[0].get('id')} status={orders[0].get('status')}")
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    asyncio.run(check_today_orders())
