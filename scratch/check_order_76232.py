from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order
with Session(engine) as s:
    o = s.exec(select(Order).where(Order.id == 76232)).first()
    if not o:
        o = s.exec(select(Order).where(Order.external_number == '76232')).first()
    if o:
        print('ORDER:', o.id, 'ext:', o.external_number, 'status:', o.status, 'iiko_id:', o.iiko_order_id, 'courier:', o.courier_name)
    else:
        print('Order 76232 not found')
