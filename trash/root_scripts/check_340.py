from app.core.database import SessionLocal
from app.models.order import Order
session = SessionLocal()
o = session.query(Order).get(340)
if o:
    print(f"ID {o.id}:")
    print(f"  City: {o.city}")
    print(f"  Street: {o.street}")
    print(f"  House: {o.house}")
    print(f"  Flat: {o.flat}")
    print(f"  Entrance: {o.entrance}")
    print(f"  Floor: {o.floor}")
    print(f"  Doorphone: {o.doorphone}")
session.close()
