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
        # Берем заказы за последние 3 дня, где время iiko значительно отстает от времени создания в нашей БД
        # Или просто прибавляем 5 часов ко всем iiko_creation_time, которые были созданы до текущего момента
        statement = select(Order).where(Order.iiko_creation_time != None)
        orders = session.exec(statement).all()
        
        count = 0
        for o in orders:
            # Прибавляем 5 часов (смещение Тюмени), так как бэкенд ошибочно вычитал их при синхронизации
            # считая входящее UTC время за местное.
            o.iiko_creation_time = o.iiko_creation_time + timedelta(hours=5)
            session.add(o)
            count += 1
            
        session.commit()
        print(f"Successfully updated {count} orders.")
except Exception as e:
    print(f"Error: {e}")
