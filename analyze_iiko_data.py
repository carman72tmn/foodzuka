import asyncio
import json
from datetime import datetime, timedelta
from app.services.iiko_service import iiko_service

async def analyze_orders():
    # За последние 2 часа
    dt_to = datetime.now()
    dt_from = dt_to - timedelta(days=2)
    
    print(f"Fetching orders from {dt_from} to {dt_to}")
    orders = await iiko_service.get_orders_by_date(dt_from, dt_to)
    
    if orders:
        print(f"Found {len(orders)} orders")
        for i, order in enumerate(orders[:3]):
            print(f"\n--- Order {i+1} (ID: {order.get('id')}) ---")
            # Выводим только важные поля для адреса
            address_data = {
                "id": order.get("id"),
                "order_type": order.get("orderType", {}).get("name"),
                "address": order.get("address"),
                "deliveryPoint": order.get("deliveryPoint"),
                "customer": order.get("customer")
            }
            print(json.dumps(address_data, indent=2, ensure_ascii=False))
    else:
        print("No orders found in last 2 hours")

if __name__ == "__main__":
    asyncio.run(analyze_orders())
