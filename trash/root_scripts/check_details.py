from app.core.database import SessionLocal
from app.models.order import Order
import json
session = SessionLocal()
o = session.query(Order).get(359)
if o:
    print(f"ID {o.id}:")
    print(f"  Customer Info Details: {o.customer_info_details}")
session.close()
