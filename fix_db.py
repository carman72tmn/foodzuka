import re
from app.core.database import SessionLocal
from app.models.order import Order
from datetime import datetime, timedelta

session = SessionLocal()
yesterday = datetime.utcnow() - timedelta(days=2)
orders = session.query(Order).filter(Order.created_at >= yesterday).all()

for o in orders:
    if o.delivery_address and "{'name':" in o.delivery_address:
        m = re.search(r"{'name':\s*'([^']*)'}", o.delivery_address)
        if m:
            o.delivery_address = o.delivery_address.replace(m.group(0), m.group(1))
            print(f"Fixed ID {o.id}: {o.delivery_address}")
    if o.city and "{'name':" in o.city:
        m = re.search(r"{'name':\s*'([^']*)'}", o.city)
        if m:
            o.city = m.group(1)
            print(f"Fixed City ID {o.id}: {o.city}")

session.commit()
session.close()
