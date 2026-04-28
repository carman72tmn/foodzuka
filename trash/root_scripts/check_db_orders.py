from app.core.database import SessionLocal
from app.models.order import Order
from sqlalchemy import desc

db = SessionLocal()
orders = db.query(Order).order_by(desc(Order.id)).limit(5).all()
db.close()

for o in orders:
    print(f"ID: {o.id}, IikoID: {o.iiko_order_id}, Number: {o.external_number}, Address: {o.delivery_address}")
