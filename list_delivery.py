from app.core.database import SessionLocal
from app.models.order import Order
session = SessionLocal()
orders = session.query(Order).filter(Order.order_type == "Доставка").order_by(Order.created_at.desc()).limit(5).all()
for o in orders:
    print(f"ID {o.id}: {o.delivery_address} (Created: {o.created_at})")
session.close()
