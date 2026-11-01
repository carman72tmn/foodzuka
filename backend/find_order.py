import json
import os
import sys
from decimal import Decimal

sys.path.append("/app")

from sqlmodel import Session, create_engine, select, or_
from app.models.order import Order
from app.core.config import settings

def find_order(search_term):
    engine = create_engine(str(settings.DATABASE_URL))
    with Session(engine) as session:
        if search_term == "recent":
            statement = select(Order).order_by(Order.created_at.desc()).limit(10)
        else:
            try:
                oid = int(search_term)
                statement = select(Order).where(Order.id == oid)
            except:
                statement = select(Order).where(Order.external_number.like(f"%{search_term}%"))
        
        orders = session.exec(statement).all()
        for o in orders:
            print("=" * 80)
            print(f"ID: {o.id} | External: {o.external_number} | Status: {o.status}")
            print(f"Iiko ID: {o.iiko_order_id}")
            print(f"Base Total: {o.total_amount} | With Disc: {o.total_with_discount}")
            print(f"Discount: {o.total_discount} | Bonus: {o.bonus_spent}")
            print(f"Left: {o.left_to_pay} | Created: {o.created_at}")
            print("-" * 80)
            
            print("DISCOUNTS:")
            print(json.dumps(o.discounts_details, indent=2, ensure_ascii=False))
            print("-" * 80)
            
            print("PAYMENTS:")
            print(json.dumps(o.payments_details, indent=2, ensure_ascii=False))
            print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        find_order(sys.argv[1])
    else:
        find_order("recent")
