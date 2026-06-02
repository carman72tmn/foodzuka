import os
import sys

# Добавляем путь к корню приложения, чтобы импорты работали
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import Session, engine
from app.models.order import Order
from sqlmodel import select

def list_discounted_orders():
    with Session(engine) as session:
        orders = session.exec(select(Order).where(Order.total_discount > 0).order_by(Order.created_at.desc())).all()
        print(f"Found {len(orders)} orders with discounts.")
        for o in orders[:20]:
            print(f"ID: {o.id} | Iiko ID: {o.iiko_order_id} | Discount: {o.total_discount} | Status: {o.status}")

if __name__ == "__main__":
    list_discounted_orders()
