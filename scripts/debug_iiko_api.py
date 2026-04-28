import asyncio
import os
import sys
import json

# Добавляем путь к приложению для импортов
sys.path.append(os.getcwd())

from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
from datetime import datetime, timedelta

async def main():
    print("Debugging iiko Cloud API Response...")
    with SessionLocal() as session:
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login
        org_id = settings_db.organization_id
        
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(hours=48) # 2 дня для теста
        
        date_format = "%Y-%m-%dT%H:%M:%S.000"
        payload = {
            "organizationIds": [org_id],
            "deliveryDateFrom": date_from.strftime(date_format),
            "deliveryDateTo": date_to.strftime(date_format),
            "statuses": ["Unconfirmed", "WaitCooking", "ReadyForCooking", "CookingStarted", "CookingCompleted", "Waiting", "OnWay", "Delivered", "Closed", "Cancelled"]
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            res = await iiko_service._request(
                "POST", "/api/1/deliveries/by_delivery_date_and_status",
                payload,
                api_login=api_login,
                organization_id=org_id
            )
            print("\nRAW RESPONSE KEYS:", res.keys())
            if "orders" in res:
                print(f"Found {len(res['orders'])} orders")
            if "deliveries" in res:
                print(f"Found {len(res['deliveries'])} deliveries")
                
            print("\nFULL RESPONSE (truncated):")
            print(json.dumps(res, indent=2)[:2000])
            
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
