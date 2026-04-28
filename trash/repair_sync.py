
import sys
import os

path = 'c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_sync_service.py'
if not os.path.exists(path):
    print(f"Error: {path} not found")
    sys.exit(1)

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line where the class prematurely ends (around the corrupted area)
cutoff = -1
for i, line in enumerate(lines):
    if 'iiko_sync_service = IikoSyncService()' in line and i > 2900:
        cutoff = i
        break

if cutoff == -1:
    print("Could not find cutoff point")
    sys.exit(1)

# Keep the file up to the cutoff (before the accidental class end)
# Note: cutoff index is the line with 'iiko_sync_service = IikoSyncService()'
# We want to keep everything BEFORE that.
clean_lines = lines[:cutoff]

new_tail = """
    # =========================================================================
    # Управление клиентской базой (Очистка и объединение)
    # =========================================================================

    async def find_customers_missing_iiko_data(self, session: Session) -> List[Customer]:
        \"\"\"Поиск клиентов, у которых отсутствует iiko_id или uid.\"\"\"
        from sqlalchemy import or_
        statement = select(Customer).where(
            or_(
                Customer.iiko_id == None,
                Customer.uid == None,
                Customer.iiko_id == "",
                Customer.uid == ""
            )
        )
        customers = session.exec(statement).all()
        logger.info(f"Найдено {len(customers)} клиентов с отсутствующими ID iiko")
        return customers

    async def merge_customers_by_uid(self, session: Session) -> Dict[str, Any]:
        \"\"\"Объединение аккаунтов с одинаковыми iiko UID.\"\"\"
        statement = select(Customer.uid).where(Customer.uid != None, Customer.uid != "").group_by(Customer.uid).having(func.count(Customer.uid) > 1)
        duplicate_uids = session.exec(statement).all()
        
        if not duplicate_uids:
            return {"success": True, "merged_groups": 0, "message": "Дубликаты по UID не найдены"}

        merged_groups_count = 0
        total_deleted = 0
        
        for uid in duplicate_uids:
            group_statement = select(Customer).where(Customer.uid == uid).order_by(Customer.id)
            customers = session.exec(group_statement).all()
            if len(customers) < 2: continue
            
            master = customers[0]
            duplicates = customers[1:]
            
            self._merge_customer_group_sync(session, master, duplicates)
            merged_groups_count += 1
            total_deleted += len(duplicates)
            
        session.commit()
        msg = f"Объединено групп: {merged_groups_count}, удалено дублей: {total_deleted}"
        logger.info(msg)
        return {"success": True, "merged_groups": merged_groups_count, "total_deleted": total_deleted, "message": msg}

    async def merge_customers_by_phone(self) -> Dict[str, Any]:
        \"\"\"Объединение аккаунтов по телефону (неблокирующее).\"\"\"
        def do_merge():
            from app.core.database import engine, Session
            with Session(engine) as session:
                statement = select(Customer.phone).group_by(Customer.phone).having(func.count(Customer.phone) > 1)
                duplicate_phones = session.exec(statement).all()
                if not duplicate_phones: return 0, 0

                merged_groups_count = 0
                total_deleted = 0
                for phone in duplicate_phones:
                    group_statement = select(Customer).where(Customer.phone == phone).order_by(Customer.id)
                    customers = session.exec(group_statement).all()
                    if len(customers) < 2: continue
                    
                    master = customers[0]
                    duplicates = customers[1:]
                    self._merge_customer_group_sync(session, master, duplicates)
                    session.commit()
                    merged_groups_count += 1
                    total_deleted += len(duplicates)
                return merged_groups_count, total_deleted

        merged_groups, total_deleted = await asyncio.to_thread(do_merge)
        msg = f"Объединено групп по телефону: {merged_groups}, удалено дублей: {total_deleted}"
        logger.info(msg)
        return {"success": True, "merged_groups": merged_groups, "total_deleted": total_deleted, "message": msg}

    def _merge_customer_group_sync(self, session: Session, master: Customer, duplicates: List[Customer]):
        \"\"\"Синхронное слияние группы дублей.\"\"\"
        from app.models.order import Order
        from app.models.customer import GuestPhone, GuestAddress, ClientAddressHistory, BonusTransaction, ClientBonusHistory
        from sqlalchemy import update
        from decimal import Decimal
        from datetime import datetime, timezone
        
        for dup in duplicates:
            logger.info(f"Слияние дубля ID={dup.id} в мастер ID={master.id}")
            session.exec(update(Order).where(Order.customer_id == dup.id).values(customer_id=master.id))
            
            for p in session.exec(select(GuestPhone).where(GuestPhone.customer_id == dup.id)).all():
                exists = session.exec(select(GuestPhone).where(GuestPhone.customer_id == master.id, GuestPhone.phone == p.phone)).first()
                if not exists and p.phone != master.phone:
                    p.customer_id = master.id
                    session.add(p)
                else:
                    session.delete(p)
            
            for a in session.exec(select(GuestAddress).where(GuestAddress.customer_id == dup.id)).all():
                exists = session.exec(select(GuestAddress).where(GuestAddress.customer_id == master.id, GuestAddress.address == a.address)).first()
                if not exists:
                    a.customer_id = master.id
                    session.add(a)
                else:
                    session.delete(a)
            
            session.exec(update(BonusTransaction).where(BonusTransaction.customer_id == dup.id).values(customer_id=master.id))
            session.exec(update(ClientBonusHistory).where(ClientBonusHistory.client_id == dup.id).values(client_id=master.id))
            session.exec(update(ClientAddressHistory).where(ClientAddressHistory.client_id == dup.id).values(client_id=master.id))
            
            if not master.vk_user_id and dup.vk_user_id: master.vk_user_id = dup.vk_user_id
            if not master.telegram_id and dup.telegram_id: master.telegram_id = dup.telegram_id
            if not master.email and dup.email: master.email = dup.email
            if not master.name or master.name == "Гость": master.name = dup.name
            if not master.surname and dup.surname: master.surname = dup.surname
            
            master.total_orders_count = (master.total_orders_count or 0) + (dup.total_orders_count or 0)
            master.total_orders_amount = (master.total_orders_amount or Decimal("0")) + (dup.total_orders_amount or Decimal("0"))
            master.total_purchases_sum = (master.total_purchases_sum or Decimal("0")) + (dup.total_purchases_sum or Decimal("0"))
            
            if dup.last_order_date and (not master.last_order_date or dup.last_order_date > master.last_order_date):
                master.last_order_date = dup.last_order_date
                master.last_iiko_order_id = dup.last_iiko_order_id
            
            session.delete(dup)
            
        master.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.add(master)
        session.flush()

iiko_sync_service = IikoSyncService()

# =========================================================================
# Точки входа для планировщика задач (Entry Points)
# =========================================================================

async def sync_all():
    \"\"\"Полная синхронизация iiko.\"\"\"
    from app.core.database import SessionLocal
    with SessionLocal() as session:
        logger.info(">>> Запуск полной синхронизации iiko")
        try:
            await iiko_sync_service.sync_categories_only(session)
            await iiko_sync_service.sync_menu(session)
            await iiko_sync_service.sync_stop_lists(session)
            await iiko_sync_service.merge_customers_by_uid(session)
            logger.info("<<< Полная синхронизация завершена")
        except Exception as e:
            logger.error(f"!!! Ошибка синхронизации: {e}", exc_info=True)

async def sync_orders_task(hours: int = 24):
    \"\"\"Синхронизация заказов.\"\"\"
    from app.core.database import SessionLocal
    with SessionLocal() as session:
        try:
            await iiko_sync_service.sync_orders(session, hours=hours)
        except Exception as e:
            logger.error(f"!!! Ошибка синхронизации заказов: {e}", exc_info=True)

async def merge_customers_task():
    \"\"\"Слияние клиентов.\"\"\"
    from app.core.database import SessionLocal
    with SessionLocal() as session:
        try:
            await iiko_sync_service.merge_customers_by_uid(session)
            await iiko_sync_service.merge_customers_by_phone()
        except Exception as e:
            logger.error(f"!!! Ошибка слияния клиентов: {e}", exc_info=True)
"""

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)
    f.write(new_tail)

print("Successfully repaired iiko_sync_service.py")
