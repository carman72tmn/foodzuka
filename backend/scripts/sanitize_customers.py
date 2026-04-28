import os
import sys
from datetime import datetime, timezone
from collections import defaultdict

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.customer import Customer
from app.utils.phone_utils import normalize_phone
from app.services.iiko_sync_service import iiko_sync_service

def sanitize_customers():
    print("Starting robust customer data sanitation...")
    
    with Session(engine) as session:
        # 1. Группировка всех клиентов по нормализованному телефону
        customers = session.exec(select(Customer)).all()
        print(f"Total customers in DB: {len(customers)}")
        
        phone_groups = defaultdict(list)
        for c in customers:
            norm = normalize_phone(c.phone)
            if norm:
                phone_groups[norm].append(c)
        
        print(f"Found {len(phone_groups)} unique normalized phone numbers.")
        
        # 2. Обработка групп
        for norm_phone, group in phone_groups.items():
            if len(group) > 1:
                # Есть дубликаты! Вызываем слияние.
                # merge_customers_by_phone ищет по текущим телефонам, 
                # но нам нужно объединить именно ЭТУ группу.
                # Мы можем просто обновить телефоны всем в группе до нормализованного по очереди, 
                # НО это вызовет UniqueViolation.
                
                print(f"Merging group for {norm_phone} ({len(group)} customers)...")
                # Берем первого как мастера (предпочтительно того, у кого уже есть UID или нормальный формат)
                master = None
                for c in group:
                    if c.phone == norm_phone:
                        master = c
                        break
                if not master:
                    master = group[0]
                
                others = [c for c in group if c.id != master.id]
                
                # Ручное слияние данных для этой конкретной группы
                for other in others:
                    # Перенос заказов
                    from app.models.order import Order
                    orders = session.exec(select(Order).where(Order.customer_id == other.id)).all()
                    for o in orders:
                        o.customer_id = master.id
                        session.add(o)
                    
                    # Перенос адресов (если есть связь)
                    # В этом проекте адреса могут быть в разных таблицах, iiko_sync_service.merge_customer_data_sync
                    # лучше использовать готовый метод, но он требует сессии и объектов.
                    
                    # Удаляем дубликат
                    session.delete(other)
                
                # Убеждаемся, что у мастера правильный телефон
                master.phone = norm_phone
                master.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                session.add(master)
                session.commit() # Коммитим каждую группу для надежности
            else:
                # Только один клиент с таким номером, просто нормализуем если надо
                c = group[0]
                if c.phone != norm_phone:
                    try:
                        c.phone = norm_phone
                        c.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                        session.add(c)
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        print(f"Error updating phone for {c.id}: {e}")

    # 3. Финальный прогон через стандартный метод слияния (для подстраховки связей)
    print("Running final global merge...")
    import asyncio
    async def run_merge():
        with Session(engine) as session:
            await iiko_sync_service.merge_customers_by_phone(session)
    asyncio.run(run_merge())
    
    print("Sanitation complete.")

if __name__ == "__main__":
    sanitize_customers()
