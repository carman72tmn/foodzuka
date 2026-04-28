from app.core.database import SessionLocal
from app.models.order import Order
session = SessionLocal()
for oid in [359, 355, 351]:
    o = session.query(Order).get(oid)
    if o:
        print(f"ID {o.id}: Type: {o.order_type}")
session.close()
