from app.core.database import SessionLocal
from app.models.order import Order
session = SessionLocal()
o = session.query(Order).get(358)
if o:
    print(f"ID {o.id}:")
    print(f"  City: {o.city}")
    print(f"  Street: {o.street}")
    print(f"  House: {o.house}")
    print(f"  Address: {o.delivery_address}")
session.close()
