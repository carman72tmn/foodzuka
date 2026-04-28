from app.core.database import SessionLocal
from app.models.employee import CourierOrder
from sqlalchemy import select
from datetime import date, datetime, timedelta

session = SessionLocal()
print("Fetching last 50 courier orders regardless of date...")
stmt = select(CourierOrder).order_by(CourierOrder.id.desc()).limit(50)
results = session.execute(stmt).all()
print(f"Total results: {len(results)}")

for row in results:
    # results from session.execute are rows
    o = row[0]
    print(f"ID: {o.id} | Num: {o.order_num} | Time: {o.actual_delivery_time} | Addr: {o.address} | Zone: {o.delivery_zone}")
