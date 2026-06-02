import json
from sqlmodel import Session, create_engine, select
from app.models.order import Order
from app.core.config import settings

def list_recent():
    engine = create_engine(str(settings.DATABASE_URL))
    with Session(engine) as session:
        orders = session.exec(select(Order).order_by(Order.id.desc()).limit(50)).all()
        for o in orders:
            print(f"ID: {o.id} | Ext: {o.external_number} | Amount: {o.total_with_discount} | Status: {o.status}")

if __name__ == "__main__":
    list_recent()
