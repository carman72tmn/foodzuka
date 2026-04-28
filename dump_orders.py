from app.models.order import Order
from sqlmodel import Session, select
from app.core.database import engine
import json

with Session(engine) as session:
    # Latest 5 delivery orders with problematic addresses
    statement = select(Order).where(Order.order_type == "Доставка").order_by(Order.id.desc()).limit(5)
    orders = session.exec(statement).all()
    
    for o in orders:
        print(f"Order ID: {o.id}")
        print(f"Iiko ID: {o.iiko_order_id}")
        print(f"Delivery Address: {o.delivery_address}")
        # Assuming we have raw data in order_items_details or customer_info_details if they were saved
        # But wait, iiko_sync_service saves o_data in order_items_details? No, it saves it in order_items_details only if explicitly coded.
        # Let's check what's in order_items_details or customer_info_details
        print(f"Customer Info Details: {json.dumps(o.customer_info_details, indent=2, ensure_ascii=False)}")
        print("-" * 50)
