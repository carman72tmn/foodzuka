from app.core.database import SessionLocal
from app.models.order import Order
session = SessionLocal()
orders = session.query(Order).order_by(Order.created_at.desc()).limit(20).all()
for o in orders:
    print(f"ID {o.id}: Type: {o.order_type} | Address: {o.delivery_address}")
session.close()
