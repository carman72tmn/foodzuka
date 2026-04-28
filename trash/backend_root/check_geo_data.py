from app.core.database import SessionLocal
from app.models.order import Order

def check():
    session = SessionLocal()
    try:
        orders = session.query(Order).order_by(Order.created_at.desc()).limit(20).all()
        print(f"{'ID':<5} | {'Created At':<30} | {'Type':<10} | {'Zone':<10}")
        print("-" * 80)
        for o in orders:
            print(f"{o.id:<5} | {str(o.created_at):<30} | {str(o.order_type):<10} | {str(o.delivery_zone):<10}")
    finally:
        session.close()

if __name__ == "__main__":
    check()
