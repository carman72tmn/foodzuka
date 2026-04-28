from app.core.database import SessionLocal
from app.models.order import Order
from sqlmodel import select

with SessionLocal() as db:
    orders = db.exec(select(Order).order_by(Order.created_at.desc()).limit(5)).all()
    print("Recent orders:")
    for o in orders:
        print(f"ID: {o.iiko_order_id} | ExtNum: {o.external_number} | Addr: {o.delivery_address} | Status: {o.status}")
