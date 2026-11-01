import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from app.core.database import SessionLocal
from app.services.iiko_sync_service import iiko_sync_service
from app.models.product import Product, ProductSize
from sqlmodel import select

async def main():
    session = SessionLocal()
    try:
        target_id = '8aff0de0-dc6a-4cea-99d2-733293122c0d' # Сборный ВОК
        
        # До синхронизации
        prod_before = session.exec(select(Product).where(Product.iiko_id == target_id)).first()
        price_before = prod_before.price if prod_before else "Не найден"
        print(f"Цена товара в БД ДО синхронизации: {price_before} руб.")
        
        # Запуск синхронизации меню
        print("Запуск синхронизации меню...")
        res = await iiko_sync_service.sync_menu(session)
        print(f"Результат синхронизации: {res}")
        
        # Обновим сессию
        session.close()
        session = SessionLocal()
        
        # После синхронизации
        prod_after = session.exec(select(Product).where(Product.iiko_id == target_id)).first()
        price_after = prod_after.price if prod_after else "Не найден"
        print(f"Цена товара в БД ПОСЛЕ синхронизации: {price_after} руб.")
        
        if prod_after:
            sizes = session.exec(select(ProductSize).where(ProductSize.product_id == prod_after.id)).all()
            print("Размеры после синхронизации:")
            for s in sizes:
                print(f" - {s.name}: {s.price} руб.")
                
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    asyncio.run(main())
