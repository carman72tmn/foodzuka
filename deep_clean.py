from app.core.database import SessionLocal
from app.models.order import Order
import re
session = SessionLocal()
orders = session.query(Order).order_by(Order.created_at.desc()).limit(200).all()
for o in orders:
    if o.delivery_address and "?" in o.delivery_address:
        # Reset to just city and let the sync service rebuild it
        o.delivery_address = o.city or "Тюмень"
        print(f"Cleaned ID {o.id}")
session.commit()
session.close()
