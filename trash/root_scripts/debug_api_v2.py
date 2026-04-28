import asyncio
import json
from app.services.iiko_service import IikoService
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

async def main():
    db = SessionLocal()
    settings = db.query(IikoSettings).first()
    db.close()
    
    if not settings:
        print("No settings found")
        return
        
    service = IikoService()
    
    # Получаем заказы за сегодня
    from datetime import datetime, timedelta
    date_from = datetime.now() - timedelta(days=1)
    date_to = datetime.now()
    
    print(f"Fetching orders from {date_from} to {date_to}...")
    orders = await service.get_orders_by_date(
        date_from=date_from,
        date_to=date_to,
        organization_id=settings.organization_id
    )
    
    if orders:
        print(f"Found {len(orders)} orders")
        # Ищем заказ 73304 или любой другой
        sample = orders[0]
        for o in orders:
            if o.get("order", {}).get("externalNumber") == "73304" or o.get("externalNumber") == "73304":
                sample = o
                break
        
        print("Sample order keys:", list(sample.keys()))
        if "order" in sample:
            print("Inner order keys:", list(sample["order"].keys()))
            print("Address from inner order:", json.dumps(sample["order"].get("address"), indent=2, ensure_ascii=False))
            print("Delivery point from inner order:", json.dumps(sample["order"].get("deliveryPoint"), indent=2, ensure_ascii=False))
        else:
            print("Address from order:", json.dumps(sample.get("address"), indent=2, ensure_ascii=False))
            print("Delivery point from order:", json.dumps(sample.get("deliveryPoint"), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
