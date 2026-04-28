import sys
import os

# Добавляем путь к приложению
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.core.database import SessionLocal

def repair():
    db = SessionLocal()
    try:
        print("Запуск полной реконструкции поврежденных адресов...")
        
        # Выбираем заказы, где в адресе или типе заказа есть знаки вопроса
        result = db.execute(text("""
            SELECT id, city, street, house, flat, entrance, floor, doorphone, order_type, delivery_address 
            FROM orders 
            WHERE delivery_address LIKE '%?%' OR order_type LIKE '%?%'
        """))
        
        updated_count = 0
        for row in result:
            o_id, city, street, house, flat, entrance, floor, doorphone, o_type, old_addr = row
            
            # 1. Исправляем тип заказа
            new_type = o_type
            if '?' in str(o_type):
                if len(str(o_type)) == 16:
                    new_type = 'Доставка'
                elif len(str(o_type)) == 18:
                    new_type = 'Самовывоз'
                elif 'Доставка' in str(o_type): # На случай частичной порчи
                    new_type = 'Доставка'
                elif 'Самовывоз' in str(o_type):
                    new_type = 'Самовывоз'
            
            # 2. Реконструируем адрес из чистых компонентов
            # Если компоненты (улица, дом) сохранились без знаков вопроса, соберем адрес заново
            if street and '?' not in str(street):
                parts = []
                if city: parts.append(city)
                if street: parts.append(street)
                if house: parts.append(f"д. {house}")
                if flat: parts.append(f"кв. {flat}")
                if entrance: parts.append(f"под. {entrance}")
                if floor: parts.append(f"эт. {floor}")
                if doorphone: parts.append(f"код {doorphone}")
                
                new_addr = ", ".join(parts)
                
                db.execute(text("UPDATE orders SET delivery_address = :addr, order_type = :otype WHERE id = :id"), 
                           {"addr": new_addr, "otype": new_type, "id": o_id})
                updated_count += 1
                print(f"Обновлен заказ {o_id}: {new_addr}")
            else:
                # Если даже улица битая, просто чистим знаки вопроса
                clean_addr = str(old_addr).replace('?', '')
                db.execute(text("UPDATE orders SET order_type = :otype, delivery_address = :addr WHERE id = :id"), 
                           {"otype": new_type, "addr": clean_addr, "id": o_id})
                updated_count += 1
                print(f"Очищен заказ {o_id} (улица повреждена)")

        db.commit()
        print(f"\nВсего обновлено/восстановлено заказов: {updated_count}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    repair()
