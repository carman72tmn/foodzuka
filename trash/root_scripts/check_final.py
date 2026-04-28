from app.core.database import SessionLocal
from app.models.order import Order
session = SessionLocal()
o = session.query(Order).get(340)
if o:
    print(f"ID {o.id}: {o.delivery_address}")
session.close()
