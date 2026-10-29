import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings
from app.models.order import Order

async def test_status():
    with Session(engine) as s:
        settings = s.exec(select(IikoSettings)).first()
        order = s.exec(select(Order).where(Order.id == 2808)).first()
        org_id = str(settings.organization_id)
        iiko_order_id = str(order.iiko_order_id)

    print('Testing change_delivery_status to OnWay in iiko Cloud...')
    try:
        res = await iiko_service.change_delivery_status(
            organization_id=org_id,
            order_id=iiko_order_id,
            delivery_status='OnWay'
        )
        print('RES STATUS OnWay:', res)
    except Exception as e:
        print('ERR STATUS:', e)

asyncio.run(test_status())
