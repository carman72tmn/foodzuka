from app.core.database import SessionLocal
from app.models.order import Order
from sqlalchemy import desc

def check_latest_orders():
    session = SessionLocal()
    try:
        # Берем 5 последних доставочных заказов
        orders = session.query(Order).filter(Order.order_type != 'Самовывоз').order_by(desc(Order.created_at)).limit(5).all()
        
        print(f"{'ID':<5} | {'Flat':<10} | {'Entr':<5} | {'Floor':<5} | {'Door':<5} | {'Address'}")
        print("-" * 80)
        for o in orders:
            print(f"{o.id:<5} | {str(o.flat):<10} | {str(o.entrance):<5} | {str(o.floor):<5} | {str(o.doorphone):<5} | {o.delivery_address}")
            
    finally:
        session.close()

if __name__ == "__main__":
    check_latest_orders()
