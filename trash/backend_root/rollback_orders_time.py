import sys
import os
from datetime import timedelta

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.getcwd())

try:
    from app.models.order import Order
    from app.core.database import SessionLocal
    from sqlmodel import select

    with SessionLocal() as session:
        statement = select(Order).where(Order.iiko_creation_time != None)
        orders = session.exec(statement).all()
        
        count = 0
        for o in orders:
            o.iiko_creation_time = o.iiko_creation_time - timedelta(hours=5)
            session.add(o)
            count += 1
            
        session.commit()
        print(f"Successfully rolled back {count} orders.")
except Exception as e:
    print(f"Error: {e}")
