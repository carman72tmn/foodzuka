from app.core.database import SessionLocal
from app.models.order import Order
from sqlmodel import select

with SessionLocal() as db:
    orders = db.exec(select(Order).order_by(Order.created_at.desc()).limit(5)).all()
    print("Recent orders in DB:")
    for o in orders:
        print(f"Created At: {o.created_at} | ID: {o.iiko_order_id} | Num: {o.external_number}")
