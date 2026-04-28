import asyncio
import json
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def main():
    order_id = "02073df5-c446-49f7-b3be-4db6cb968751" # Тот самый ID из теста
    
    with SessionLocal() as session:
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login
        org_id = settings_db.organization_id
        
        print(f"Inspecting order {order_id} for org {org_id}...")
        
        # Запрашиваем детализацию заказа
        res = await iiko_service._request(
            "POST", "/api/1/deliveries/by_id",
            {"organizationId": org_id, "orderIds": [order_id]},
            api_login=api_login,
            organization_id=org_id
        )
        
        print("FULL ORDER JSON:")
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
