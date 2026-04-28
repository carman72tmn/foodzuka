import asyncio
import json
from sqlmodel import Session, select
from app.core.database import engine
from app.services.iiko_service import iiko_service
from app.models.iiko_settings import IikoSettings

async def inspect():
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        order_id = "c40a8982-ebb0-4246-91b6-0608efbd3005"
        org_id = settings.organization_id
        
        print(f"Fetching raw data for order {order_id}...")
        data = await iiko_service.get_order_by_id(order_id, org_id, api_login=settings.api_login)
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(inspect())
