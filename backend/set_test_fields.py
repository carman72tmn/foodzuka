from app.core.database import SessionLocal
from app.models.order import Order

def set_test():
    session = SessionLocal()
    try:
        # Берем последний заказ
        order = session.query(Order).order_by(Order.id.desc()).first()
        if order:
            order.address_comment = "ТЕСТ: Домофон 123#, 3 этаж, лифт работает"
            order.additional_info = "ТЕСТ: Позвонить за 10 минут"
            order.other_info = "ТЕСТ: Бесконтактная доставка"
            session.commit()
            print(f"Successfully set test fields for order {order.id} (Num: {order.external_number})")
        else:
            print("No orders found")
    finally:
        session.close()

if __name__ == "__main__":
    set_test()
