
import asyncio
import os
import sys
import json
from decimal import Decimal

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import get_db_context
from app.models.order import Order

async def debug_order(order_ref):
    async with get_db_context() as db:
        # Try finding by external_number or id
        order = await db.get(Order, order_ref)
        if not order:
            from sqlalchemy import select
            result = await db.execute(select(Order).where(Order.external_number == str(order_ref)))
            order = result.scalars().first()
        
        if not order:
            print(f"Order {order_ref} not found.")
            return

        print(f"Order ID: {order.id}")
        print(f"External Number: {order.external_number}")
        print(f"Total Amount: {order.total_amount}")
        print(f"Total Discount: {order.total_discount}")
        print(f"Total With Discount: {order.total_with_discount}")
        print(f"Total Paid: {order.total_paid}")
        print(f"Left To Pay: {order.left_to_pay}")
        print(f"Payments Data (RAW): {order.payments_data}")
        
        if order.payments_data:
            payments = order.payments_data if isinstance(order.payments_data, list) else json.loads(order.payments_data)
            print("\nPayments List:")
            for p in payments:
                print(f" - Type: {p.get('paymentTypeKind')}, Sum: {p.get('sum')}, Status: {p.get('status')}")

if __name__ == "__main__":
    order_ref = "186" # User said "заказа 186 73577"
    asyncio.run(debug_order(order_ref))
    # Also try the other one just in case
    asyncio.run(debug_order(73577))
