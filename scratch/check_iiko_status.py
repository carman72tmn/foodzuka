import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings

async def check():
    with Session(engine) as s:
        settings = s.exec(select(IikoSettings)).first()
        org_id = str(settings.organization_id)
        order_id = 'dd1d802e-3219-453b-ba5e-2064fd694a75'
    
    order_data = await iiko_service.get_order_by_id(order_id, organization_id=org_id)
    ord_info = order_data.get('order', order_data)
    print('Order status in iiko:', ord_info.get('status'), 'deliveryStatus:', ord_info.get('deliveryStatus'), 'courierInfo:', ord_info.get('courierInfo'))

asyncio.run(check())
