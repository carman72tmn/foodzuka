import sys
import json
from decimal import Decimal
from sqlmodel import Session, create_engine, select
from app.models.order import Order
from app.core.config import settings

def check_order(order_id_or_num):
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        query = select(Order).where(
            (Order.id == (int(order_id_or_num) if order_id_or_num.isdigit() else -1)) |
            (Order.external_number == order_id_or_num) |
            (Order.iiko_order_id == order_id_or_num)
        )
        order = session.exec(query).first()

        if not order:
            print(f"Order {order_id_or_num} not found")
            return

        print(f"Order ID: {order.id}")
        print(f"External Number: {order.external_number}")
        print(f"iiko_order_id: {order.iiko_order_id}")
        print(f"Status: {order.status}")
        print(f"Total Amount (Base): {order.total_amount}")
        print(f"Total Discount (Net): {order.total_discount}")
        print(f"Bonus Spent: {order.bonus_spent}")
        print(f"Total With Discount (To Pay): {order.total_with_discount}")
        print(f"Left to Pay: {order.left_to_pay}")
        print(f"Is Paid: {order.is_paid}")
        print(f"Payment Method: {order.payment_method}")
        
        print("\n--- Discounts Details ---")
        print(json.dumps(order.discounts_details, indent=2, ensure_ascii=False))
        
        print("\n--- Payments Details ---")
        print(json.dumps(order.payments_details, indent=2, ensure_ascii=False))
        
        print("\n--- Summary Calculation Check ---")
        print(f"  Base Amount: {order.total_amount}")
        print(f"  - Net Discount: {order.total_discount}")
        print(f"  - Bonus Spent: {order.bonus_spent}")
        base = float(order.total_amount or 0)
        disc = float(order.total_discount or 0)
        bonus = float(order.bonus_spent or 0)
        expected = base - disc - bonus
        print(f"  = Expected To Pay: {expected}")
        print(f"  Actual To Pay: {order.total_with_discount}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_order.py <order_id_or_num>")
    else:
        check_order(sys.argv[1])
