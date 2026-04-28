from app.core.database import engine
from app.models.employee import CourierOrder
from sqlmodel import Session, select
from datetime import datetime
with Session(engine) as s:
    count = s.exec(select(CourierOrder).where(CourierOrder.actual_delivery_time >= '2026-04-20')).all()
    print(f"Count since April 20: {len(count)}")
    for o in sorted(count, key=lambda x: x.actual_delivery_time, reverse=True)[:10]:
        print(f"ID: {o.order_num}, Time: {o.actual_delivery_time}, Courier: {o.employee_id}")
