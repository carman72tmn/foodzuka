import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings
from app.models.order import Order

async def test():
    with Session(engine) as s:
        settings = s.exec(select(IikoSettings)).first()
        order = s.exec(select(Order).where(Order.id == 2808)).first()
        org_id = str(settings.organization_id)
        iiko_order_id = str(order.iiko_order_id)
        courier_id = '9170eede-0fb4-450d-88e7-6632ec6443ae' # Сергей Доставка

    print('Testing assign courier in iiko Cloud...')
    print('org_id:', org_id)
    print('order_id:', iiko_order_id)
    print('courier_id:', courier_id)

    # Тест 1: /api/1/deliveries/update_order_courier
    try:
        payload1 = {
            'organizationId': org_id,
            'orderId': iiko_order_id,
            'employeeId': courier_id
        }
        res1 = await iiko_service._request('POST', '/api/1/deliveries/update_order_courier', payload1, organization_id=org_id)
        print('RES 1 (update_order_courier):', res1)
    except Exception as e:
        print('ERR 1:', e)

    # Тест 2: /api/1/deliveries/assign_courier
    try:
        payload2 = {
            'organizationId': org_id,
            'orderId': iiko_order_id,
            'courierId': courier_id
        }
        res2 = await iiko_service._request('POST', '/api/1/deliveries/assign_courier', payload2, organization_id=org_id)
        print('RES 2 (assign_courier):', res2)
    except Exception as e:
        print('ERR 2:', e)

asyncio.run(test())
