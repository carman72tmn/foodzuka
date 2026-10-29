from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order, OrderStatus

session = Session(engine)
active_statuses = [
    OrderStatus.new,
    OrderStatus.unconfirmed,
    OrderStatus.confirmed,
    OrderStatus.preparing,
    OrderStatus.cooking,
    OrderStatus.assembling
]
active_orders = session.exec(select(Order).where(Order.status.in_(active_statuses))).all()
print(f"Active orders count: {len(active_orders)}")
for o in active_orders:
    print(f"Order ID: {o.id}, Status: {o.status}, Type: {o.order_type}")
