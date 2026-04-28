import sys
sys.path.append("/app")

from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order

def check_orders():
    with Session(engine) as session:
        orders = session.exec(select(Order).order_by(Order.id.desc()).limit(10)).all()
        for o in orders:
            print(f"Order {o.external_number}: Revision {o.revision}")

if __name__ == "__main__":
    check_orders()
