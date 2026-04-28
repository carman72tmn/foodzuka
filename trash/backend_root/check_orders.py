import sys
import os

# Добавляем путь к приложению
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.core.database import SessionLocal

def check():
    db = SessionLocal()
    try:
        print("Текущие последние заказы:")
        result = db.execute(text("SELECT id, order_type, delivery_address FROM orders ORDER BY id DESC LIMIT 5"))
        for row in result:
            print(f"ID: {row[0]} | Тип: {row[1]} | Адрес: {row[2]}")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
