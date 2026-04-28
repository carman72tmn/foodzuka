from app.core.database import SessionLocal
from app.models.order import Order
session = SessionLocal()
for oid in [359, 355, 351]:
    o = session.query(Order).get(oid)
    if o:
        print(f"ID {o.id}:")
        print(f"  City: {o.city}")
        print(f"  Address: {o.delivery_address}")
        print(f"  Street: {o.street}")
        print(f"  House: {o.house}")
        print(f"  Flat: {o.flat}")
session.close()
