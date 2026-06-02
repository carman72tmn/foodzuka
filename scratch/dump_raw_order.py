import json
import os
import sys

sys.path.append("/app")

from sqlmodel import Session, create_engine, select
from app.models.order import Order
from app.core.config import settings

def dump_raw():
    engine = create_engine(str(settings.DATABASE_URL))
    with Session(engine) as session:
        statement = select(Order).where(Order.id == 181)
        o = session.exec(statement).first()
        if o:
            # Мы не храним полный o_data в БД, но у нас есть order_items_details, discounts_details, payments_details
            print("DISCOUNTS IN DB:")
            print(json.dumps(o.discounts_details, indent=2, ensure_ascii=False))
            print("PAYMENTS IN DB:")
            print(json.dumps(o.payments_details, indent=2, ensure_ascii=False))
        else:
            print("Order 181 not found")

if __name__ == "__main__":
    dump_raw()
