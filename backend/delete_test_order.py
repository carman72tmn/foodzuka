import sys
sys.path.append("/app")
from app.core.database import SessionLocal
from app.models.order import Order, OrderItem

session = SessionLocal()
order_id = 1586

# Удаляем связанные позиции заказа
items_deleted = session.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
print(f"Deleted {items_deleted} order items.")

# Удаляем сам заказ
order_deleted = session.query(Order).filter(Order.id == order_id).delete()
print(f"Deleted {order_deleted} order.")

session.commit()
print("Delete transaction committed successfully.")
