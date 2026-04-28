import json
from app.core.database import SessionLocal
from app.models.order import Order

db = SessionLocal()
orders = db.query(Order).filter(Order.order_type == "Доставка").order_by(Order.id.desc()).limit(5).all()
if orders:
    results = []
    for order in orders:
        data = {
            "id": order.id,
            "delivery_address": order.delivery_address,
            "street": order.street,
            "house": order.house,
            "flat": order.flat,
            "entrance": order.entrance,
            "floor": order.floor,
            "order_type": order.order_type,
            "city": order.city,
            "iiko_order_id": order.iiko_order_id,
            "created_at": str(order.created_at),
            "updated_at": str(order.updated_at)
        }
        results.append(data)
    print(json.dumps(results, indent=2, ensure_ascii=False))
else:
    print("Заказы с доставкой не найдены")
db.close()
