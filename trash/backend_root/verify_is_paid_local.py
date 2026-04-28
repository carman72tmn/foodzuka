import os
from sqlmodel import Session, create_engine, select
from app.models.order import Order

# Use localhost instead of db for local execution
DATABASE_URL = "postgresql://foodtech_user:postgres@localhost:5432/foodtech_db"
engine = create_engine(DATABASE_URL)

def verify_is_paid():
    with Session(engine) as session:
        orders = session.exec(select(Order).order_by(Order.created_at.desc()).limit(10)).all()
        print(f"{'ID':<5} | {'Source':<10} | {'Is Paid':<8} | {'Status':<12} | {'Total':<10}")
        print("-" * 55)
        for o in orders:
            print(f"{o.id:<5} | {str(o.source):<10} | {str(o.is_paid):<8} | {str(o.status):<12} | {o.total_amount:<10}")

if __name__ == "__main__":
    try:
        verify_is_paid()
    except Exception as e:
        print(f"Error: {e}")
