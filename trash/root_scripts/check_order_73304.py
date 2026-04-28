from app.core.database import SessionLocal
from app.models.order import Order

db = SessionLocal()
order = db.query(Order).filter(Order.external_number == "73304").first()
db.close()

if order:
    print(f"Order {order.id} (Number: {order.external_number})")
    print(f"Street: {order.street}")
    print(f"House: {order.house}")
    print(f"Delivery Address: {order.delivery_address}")
else:
    print("Order not found")
