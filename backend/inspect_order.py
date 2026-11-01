import json
from sqlmodel import Session, create_engine, select
from app.models.order import Order
from app.core.config import settings

def inspect_order(order_id):
    engine = create_engine(str(settings.DATABASE_URL))
    with Session(engine) as session:
        order = session.exec(select(Order).where(Order.id == order_id)).first()
        if not order:
            print(f"Order {order_id} not found")
            return
        
        # Выводим основные поля для диагностики
        data = {
            "id": order.id,
            "external_number": order.external_number,
            "total_amount": str(order.total_amount),
            "total_discount": str(order.total_discount),
            "bonus_spent": str(order.bonus_spent),
            "total_with_discount": str(order.total_with_discount),
            "base_amount": str(order.base_amount),
            "left_to_pay": str(order.left_to_pay),
            "discounts_details": order.discounts_details,
            "payments_details": order.payments_details,
            "order_items_details": order.order_items_details,
            "status": order.status,
            "created_at": str(order.created_at)
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    import sys
    oid = int(sys.argv[1]) if len(sys.argv) > 1 else 73569
    inspect_order(oid)
