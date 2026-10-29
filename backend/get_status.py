from app.core.database import engine
from sqlmodel import Session
from app.models.order import Order

session = Session(engine)
order = session.get(Order, 1582)
if order:
    print("STATUS:", order.status)
else:
    print("Order 1582 not found")
