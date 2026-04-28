from app.core.database import SessionLocal
from app.models.order import Order
session = SessionLocal()
o = session.query(Order).get(340)
if o:
    print(f"Iiko ID: {o.iiko_order_id}")
    print(f"Org ID: {o.branch_id}") # Usually branch_id is mapped to org? No, organization_id is in iiko_settings
session.close()
