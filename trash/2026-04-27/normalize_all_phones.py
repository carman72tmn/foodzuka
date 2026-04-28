"""
Скрипт для массовой нормализации телефонов в БД и объединения дублей.
Версия 3: Полная перепривязка всех связанных сущностей (адреса, телефоны, история).
"""
import os
import sys
from sqlmodel import Session, select, func
from decimal import Decimal

# Добавляем путь к бэкенду, чтобы импортировать модели
sys.path.append(os.path.join(os.getcwd(), "backend"))
sys.path.append(os.getcwd())

from app.core.database import engine
from app.models.customer import Customer, GuestPhone, GuestAddress, ClientAddressHistory, BonusTransaction, ClientBonusHistory
from app.models.order import Order
from app.utils.phone_utils import normalize_phone

def merge_customers(keep: Customer, delete: Customer, session: Session):
    """Объединяет два аккаунта: переносит ВСЕ данные из delete в keep"""
    print(f"Merging IDs: {delete.id} -> {keep.id} (Phone: {keep.phone})")
    
    # 1. Бонусы
    if delete.bonus_points:
        keep.bonus_points = (keep.bonus_points or Decimal("0")) + (delete.bonus_points or Decimal("0"))
    
    # 2. Заказы
    orders = session.exec(select(Order).where(Order.customer_id == delete.id)).all()
    for order in orders:
        order.customer_id = keep.id
        session.add(order)
        
    # 3. Дополнительные телефоны
    d_phones = session.exec(select(GuestPhone).where(GuestPhone.customer_id == delete.id)).all()
    for p in d_phones:
        exists = session.exec(select(GuestPhone).where(GuestPhone.customer_id == keep.id, GuestPhone.phone == p.phone)).first()
        if not exists and p.phone != keep.phone:
            p.customer_id = keep.id
            session.add(p)
        else:
            session.delete(p)
            
    # 4. Адреса
    d_addrs = session.exec(select(GuestAddress).where(GuestAddress.customer_id == delete.id)).all()
    for a in d_addrs:
        exists = session.exec(select(GuestAddress).where(GuestAddress.customer_id == keep.id, GuestAddress.address == a.address)).first()
        if not exists:
            a.customer_id = keep.id
            session.add(a)
        else:
            session.delete(a)
            
    # 5. История адресов (Laravel compat)
    d_hists = session.exec(select(ClientAddressHistory).where(ClientAddressHistory.client_id == delete.id)).all()
    for h in d_hists:
        h.client_id = keep.id
        session.add(h)
        
    # 6. Транзакции бонусов
    d_trans = session.exec(select(BonusTransaction).where(BonusTransaction.customer_id == delete.id)).all()
    for t in d_trans:
        t.customer_id = keep.id
        session.add(t)
        
    # 7. История бонусов (Laravel compat)
    d_bhist = session.exec(select(ClientBonusHistory).where(ClientBonusHistory.client_id == delete.id)).all()
    for bh in d_bhist:
        bh.client_id = keep.id
        session.add(bh)
        
    # 8. Мета-данные
    if delete.telegram_id and not keep.telegram_id: keep.telegram_id = delete.telegram_id
    if delete.vk_user_id and not keep.vk_user_id: keep.vk_user_id = delete.vk_user_id
    if delete.email and not keep.email: keep.email = delete.email
    if delete.iiko_customer_id and not keep.iiko_customer_id:
        keep.iiko_customer_id = delete.iiko_customer_id
        keep.iiko_id = delete.iiko_id
        keep.uid = delete.uid
        
    # 9. Удаление дубликата
    session.delete(delete)
    session.add(keep)
    session.flush()

def run_normalization():
    with Session(engine) as session:
        # Сначала нормализуем все телефоны, где нет конфликтов
        all_customers = session.exec(select(Customer).order_by(Customer.id)).all()
        print(f"Phase 1: Normalizing phones. Total customers: {len(all_customers)}")
        
        for c in all_customers:
            norm = normalize_phone(c.phone)
            if not norm or c.phone == norm:
                continue
            
            # Проверяем, не занят ли уже этот norm
            exists = session.exec(select(Customer).where(Customer.phone == norm)).first()
            if exists:
                # Конфликт будет обработан во второй фазе (слияние)
                continue
            
            print(f"Updating ID {c.id}: {c.phone} -> {norm}")
            c.phone = norm
            session.add(c)
            session.flush()
        
        session.commit()
        
        # Фаза 2: Слияние дубликатов
        print("Phase 2: Merging duplicates...")
        # Ищем все нормализованные номера, которые встречаются > 1 раза
        # Но так как мы еще не все нормализовали, лучше просто пройтись по всем и искать дубли через normalize_phone
        
        all_customers = session.exec(select(Customer).order_by(Customer.id)).all()
        processed_ids = set()
        
        for c in all_customers:
            if c.id in processed_ids: continue
            
            norm = normalize_phone(c.phone)
            if not norm: continue
            
            # Ищем всех, кто после нормализации имеет такой же номер
            # Это сложнее сделать одним SQL запросом, поэтому ищем в цикле (не эффективно, но надежно для разовой акции)
            # Хотя стоп, мы уже нормализовали всё что могли в фазе 1.
            # Теперь дубликаты - это те, у кого phone РАЗНЫЕ, но normalize_phone(phone) ОДИНАКОВЫЙ.
            
            duplicates = []
            for other in all_customers:
                if other.id == c.id or other.id in processed_ids: continue
                if normalize_phone(other.phone) == norm:
                    duplicates.append(other)
            
            if duplicates:
                master = c
                # Если у кого-то из дублей есть iiko_id, а у мастера нет - меняем ролями
                for d in duplicates:
                    if d.iiko_customer_id and not master.iiko_customer_id:
                        master = d
                
                # Убеждаемся что у мастера нормализованный номер
                master.phone = norm
                session.add(master)
                
                for slave in duplicates:
                    if slave.id == master.id: continue
                    merge_customers(master, slave, session)
                    processed_ids.add(slave.id)
            
            processed_ids.add(c.id)
            
        session.commit()
        print("Normalization and merging finished.")

if __name__ == "__main__":
    run_normalization()
