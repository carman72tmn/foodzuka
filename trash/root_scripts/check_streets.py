import json
from app.core.database import SessionLocal
from app.models.order import Order

db = SessionLocal()
orders = db.query(Order).filter(Order.street != None).order_by(Order.id.desc()).limit(10).all()
if orders:
    results = []
    for order in orders:
        data = {
            "id": order.id,
            "delivery_address": order.delivery_address,
            "street": order.street,
            "order_type": order.order_type,
            "created_at": str(order.created_at)
        }
        results.append(data)
    print(json.dumps(results, indent=2, ensure_ascii=False))
else:
    print("Заказы с заполненной улицей не найдены")
db.close()
