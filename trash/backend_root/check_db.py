from app.core.database import SessionLocal
from app.models.employee import CourierOrder
from sqlalchemy import select
from datetime import date, datetime, timedelta

session = SessionLocal()
# filter by range to avoid cast issues
today_start = datetime.combine(date.today(), datetime.min.time())
today_end = today_start + timedelta(days=1)

print(f"Checking orders from {today_start} to {today_end}")

stmt = select(CourierOrder).where(CourierOrder.actual_delivery_time >= today_start).where(CourierOrder.actual_delivery_time < today_end)
orders = session.exec(stmt).all()
print(f"Orders today: {len(orders)}")
for o in orders[:20]:
    print(f"Num: {o.order_num} | Addr: {o.address} | Zone: {o.delivery_zone}")

if len(orders) == 0:
    print("No orders for today in CourierOrder table. Checking last 5 entries:")
    last_orders = session.exec(select(CourierOrder).order_by(CourierOrder.id.desc()).limit(5)).all()
    for o in last_orders:
        print(f"ID: {o.id} | Num: {o.order_num} | Time: {o.actual_delivery_time} | Addr: {o.address}")
