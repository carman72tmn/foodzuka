from app.core.database import SessionLocal
from app.models.employee import CourierOrder
from sqlmodel import select

with SessionLocal() as session:
    orders = session.exec(select(CourierOrder)).all()
    print(f"Total courier orders: {len(orders)}")
    for o in orders[:20]:
        print(f"Order: {o.order_num}, Zone: {o.delivery_zone}, Courier: {o.employee_id}, Amount: {o.amount}")
