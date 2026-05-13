import asyncio
from app.tasks.customer_tasks import _sync_single_customer
from app.core.database import SessionLocal
from app.models.order import Order
import sys

def sync_order(order_id):
    db = SessionLocal()
    order = db.get(Order, order_id)
    if not order:
        print(f"Order {order_id} not found")
        return
    print(f"Syncing customer {order.customer_phone} for order {order_id}")
    # _sync_single_customer is async
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(_sync_single_customer(db, order.customer_phone, order_id=order_id))
    print(f"Done, success: {success}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sync_order(int(sys.argv[1]))
    else:
        print("Usage: python sync_order_manual.py <order_id>")
