import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.getcwd())

try:
    from app.models.order import Order
    from app.core.database import SessionLocal
    from sqlmodel import select

    with SessionLocal() as session:
        statement = select(Order).order_by(Order.id.desc()).limit(1)
        o = session.exec(statement).first()
        if o:
            print(f"Order ID: {o.id}")
            print(f"External Number: {o.external_number}")
            print(f"Iiko Creation Time: {o.iiko_creation_time}")
            print(f"Created At: {o.created_at}")
        else:
            print("No orders found in database.")
except Exception as e:
    print(f"Error: {e}")
