from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order
import json

with Session(engine) as session:
    orders = session.exec(select(Order).where(Order.order_type == "Доставка").order_by(Order.created_at.desc()).limit(5)).all()
    print("Recent delivery orders:")
    for o in orders:
        print(f"ID={o.id}, IIKO_ID={o.iiko_order_id}, NUM={o.external_number}, STATUS={o.status}, PM={o.payment_method}, SUM={o.total_amount}, LEFT={o.left_to_pay}, PAID={o.is_paid}")
        print(f"  payments_details: {json.dumps(o.payments_details, ensure_ascii=False)}")
