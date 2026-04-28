import sys
sys.path.insert(0, '/app')
from app.core.database import SessionLocal
from app.models.employee import CourierOrder
from sqlmodel import select

with SessionLocal() as session:
    count = len(session.exec(select(CourierOrder)).all())
    print(f"Total CourierOrders: {count}")
    if count > 0:
        latest = session.exec(select(CourierOrder).order_by(CourierOrder.id.desc())).first()
        print(f"Latest: OrderNum={latest.order_num}, CourierID={latest.employee_id}, Zone={latest.delivery_zone}, Address={latest.address}")
