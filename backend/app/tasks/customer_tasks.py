"""
Задачи Celery для работы с клиентами
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, date, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import time

from sqlmodel import Session, select
from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.customer import Customer
from app.models.sync_log import SyncStatus
from app.models.system_log import SystemLog
from sqlalchemy.orm import configure_mappers
import app.models # Важно для регистрации всех мапперов
from app.services.iiko_service import iiko_service

# Форсируем инициализацию мапперов для Celery
try:
    configure_mappers()
except Exception as e:
    print(f"Mapper configuration warning: {e}")

logger = logging.getLogger(__name__)

from app.models.customer import GuestAddress, BonusTransaction, BonusTransactionType
import re

def _parse_extra_phones(text: str) -> List[str]:
    """Парсинг дополнительных номеров телефонов из текста (заметки/комментарии)"""
    if not text:
        return []
    # Ищем номера телефонов в форматах 7xxxxxxxxxx, 8xxxxxxxxxx, +7xxxxxxxxxx
    phone_pattern = re.compile(r'(?:\+7|7|8)[\s\-\(]*(\d{3})[\s\-\)]*(\d{3})[\s\-]*(\d{2})[\s\-]*(\d{2})')
    matches = phone_pattern.findall(text)
    phones = []
    for m in matches:
        clean_phone = f"7{m[0]}{m[1]}{m[2]}{m[3]}"
        phones.append(clean_phone)
    return list(set(phones))

async def _sync_guest_addresses(session: Session, customer_id: int, addresses_data: List[Dict[str, Any]]):
    """Синхронизация адресов гостя в таблицу guest_addresses"""
    if not addresses_data:
        return
    
    # Получаем существующие адреса
    existing_addresses = session.exec(
        select(GuestAddress).where(GuestAddress.customer_id == customer_id)
    ).all()
    existing_strs = {a.address for a in existing_addresses}
    
    for addr in addresses_data:
        # Сборка адреса из компонентов iiko
        city = addr.get("city", "")
        street = addr.get("street", "")
        house = addr.get("house", "")
        flat = addr.get("flat", "")
        entrance = addr.get("entrance", "")
        floor = addr.get("floor", "")
        
        parts = []
        if city: parts.append(city)
        if street: parts.append(street)
        if house: parts.append(f"д. {house}")
        if flat: parts.append(f"кв. {flat}")
        if entrance: parts.append(f"под. {entrance}")
        if floor: parts.append(f"эт. {floor}")
        
        full_address = ", ".join(parts)
        
        if not full_address or full_address in existing_strs:
            continue
            
        new_addr = GuestAddress(
            customer_id=customer_id,
            address=full_address,
            is_main=addr.get("isPrimary", False)
        )
        session.add(new_addr)
        
        # Наполнение новой таблицы client_addresses_history (Laravel)
        from app.models.customer import ClientAddressHistory
        
        # Ищем, есть ли уже такой адрес по компонентам
        existing_history = session.exec(
            select(ClientAddressHistory).where(
                ClientAddressHistory.client_id == customer_id,
                ClientAddressHistory.city == city,
                ClientAddressHistory.street == street,
                ClientAddressHistory.house == house
            )
        ).first()
        
        if not existing_history:
            new_history = ClientAddressHistory(
                client_id=customer_id,
                city=city,
                street=street,
                house=house,
                apartment=flat,
                address=full_address,
                last_used_at=datetime.now(timezone.utc).replace(tzinfo=None),
                orders_count=1
            )
            session.add(new_history)
        else:
            existing_history.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
            existing_history.orders_count += 1
            existing_history.address = full_address
            session.add(existing_history)

        existing_strs.add(full_address)

async def _sync_guest_phones(session: Session, customer_id: int, phones: List[str], main_phone: str):
    """Синхронизация дополнительных телефонов гостя"""
    if not phones:
        return
        
    from app.models.customer import GuestPhone
    
    # Получаем существующие доп. телефоны
    existing_phones = session.exec(
        select(GuestPhone).where(GuestPhone.customer_id == customer_id)
    ).all()
    existing_nums = {p.phone for p in existing_phones}
    existing_nums.add(main_phone) # Основной телефон не считаем дополнительным
    
    for p_num in phones:
        if p_num in existing_nums:
            continue
            
        new_phone = GuestPhone(
            customer_id=customer_id,
            phone=p_num,
            comment="Из комментария iiko"
        )
        session.add(new_phone)
        existing_nums.add(p_num)

async def _sync_bonus_history(session: Session, customer_id: int, iiko_customer_id: str):
    """Синхронизация истории бонусов за последние 12 месяцев (без затирания)"""
    from datetime import timedelta
    date_from = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S.000")
    
    try:
        history = await iiko_service.get_customer_bonus_history(iiko_customer_id, date_from)
        transactions = history.get("transactions", [])
        
        for tx in transactions:
            tx_date_str = tx.get("date")
            if not tx_date_str: continue
            
            try:
                tx_date = datetime.fromisoformat(tx_date_str.replace(" ", "T"))
            except:
                continue
                
            tx_id = tx.get("id")
            amount = Decimal(str(tx.get("sum", 0)))
            tx_type = BonusTransactionType.ACCRUAL if amount > 0 else BonusTransactionType.DEDUCTION
            
            # Проверка по external_id если он есть, иначе по классическим полям
            if tx_id:
                existing = session.exec(
                    select(BonusTransaction).where(BonusTransaction.external_id == tx_id)
                ).first()
            else:
                existing = session.exec(
                    select(BonusTransaction).where(
                        BonusTransaction.customer_id == customer_id,
                        BonusTransaction.transaction_date == tx_date,
                        BonusTransaction.amount == abs(amount)
                    )
                ).first()
            
            if not existing:
                new_tx = BonusTransaction(
                    customer_id=customer_id,
                    transaction_date=tx_date,
                    type=tx_type,
                    amount=abs(amount),
                    balance_after=Decimal(str(tx.get("balanceAfter", 0))),
                    comment=tx.get("comment"),
                    order_id=tx.get("orderId"),
                    external_id=tx_id
                )
                session.add(new_tx)
                
                # Наполнение новой таблицы client_bonus_history (Laravel)
                from app.models.customer import ClientBonusHistory
                new_cbh = ClientBonusHistory(
                    client_id=customer_id,
                    type=tx_type.value,
                    amount=abs(amount),
                    transaction_date=tx_date,
                    comment=tx.get("comment")
                )
                session.add(new_cbh)
    except Exception as e:
        logger.error(f"Error syncing bonus history for {iiko_customer_id}: {e}")

async def _sync_single_customer(session: Session, phone: str, organization_id: Optional[str] = None) -> bool:
    """Прокси для вызова синхронизации из iiko_sync_service"""
    from app.services.iiko_sync_service import iiko_sync_service
    return await iiko_sync_service.sync_single_customer(session, phone, organization_id)



from app.services.import_service import import_service
import os

@celery_app.task(bind=True, name="app.tasks.customer_tasks.sync_customers_batch")
def sync_customers_batch(self, skip: int, status_id: int, force_update: bool = False):
    """
    Пакетная синхронизация клиентов (по 10 штук с паузой 30 сек)
    Если force_update=True, обновляет данные существующих клиентов.
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    take = 10
    try:
        # 0. Проверка статуса (пауза или отмена)
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if not status or status.status == "cancelled":
                logger.info(f"Task {status_id} was cancelled")
                return "Cancelled"
            
            if status.is_paused:
                logger.info(f"Task {status_id} is paused, rescheduling in 30s")
                sync_customers_batch.apply_async(
                    args=[skip, status_id, force_update],
                    countdown=30
                )
                return f"Paused at skip {skip}"

        # 1. Получаем пачку клиентов из iiko
        logger.info(f"Fetching customers from iiko: skip={skip}, take={take}")
        iiko_data = loop.run_until_complete(iiko_service.get_customers(skip=skip, take=take))
        
        customers_from_iiko = iiko_data.get("customers", [])
        if not isinstance(customers_from_iiko, list):
            logger.warning(f"Unexpected response format from iiko get_customers: {type(customers_from_iiko)}")
            customers_from_iiko = []
            
        count_received = len(customers_from_iiko)
        logger.info(f"Received {count_received} customers from iiko")
        
        added = 0
        updated = 0
        skipped = 0
        
        # 2. Обрабатываем полученных клиентов
        with Session(engine) as session:
            for c_data in customers_from_iiko:
                phone = c_data.get("phone")
                if not phone:
                    continue
                
                # Нормализация телефона через единую утилиту
                from app.utils.phone_utils import normalize_phone
                clean_phone = normalize_phone(phone)
                
                if not clean_phone:
                    continue
                
                existing = session.exec(select(Customer).where(Customer.phone == clean_phone)).first()
                
                if existing and not force_update:
                    skipped += 1
                    continue
                
                if loop.run_until_complete(_sync_single_customer(session, clean_phone)):
                    if existing:
                        updated += 1
                    else:
                        added += 1
            
            # 3. Обновляем статус
            status = session.get(SyncStatus, status_id)
            if status:
                status.processed_count += count_received
                status.added_count += added
                status.updated_count += updated
                status.updated_at = datetime.now(timezone.utc)
                
                if count_received < take:
                    status.status = "completed"
                    logger.info(f"Customer sync completed. Added: {status.added_count}, Updated: {status.updated_count}")
                    
                    sys_log = SystemLog(
                        level="INFO",
                        module="Celery:sync_customers_batch",
                        message=f"Пакетная синхронизация завершена. Добавлено: {status.added_count}, Обновлено: {status.updated_count}",
                        stack_trace=None
                    )
                    session.add(sys_log)
                
                session.add(status)
                session.commit()
                
                # 4. Если нужно продолжать
                if count_received == take:
                    logger.info(f"Scheduling next batch: skip={skip + take} in 30 seconds")
                    sync_customers_batch.apply_async(
                        args=[skip + take, status_id, force_update],
                        countdown=30
                    )
        
        return f"Processed {count_received} (Added: {added}, Updated: {updated}, Skipped: {skipped}) at skip {skip}"

        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"!!! КРИТИЧЕСКАЯ ОШИБКА ПАКЕТНОЙ СИНХРОНИЗАЦИИ (skip={skip}) !!!")
        logger.error(f"Ошибка: {str(e)}")
        
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "error"
                status.details = f"Синхронизация остановлена на skip={skip} из-за ошибки: {str(e)}"
                session.add(status)
                session.commit()
                
        # Логируем ошибку в системный лог
        with Session(engine) as session:
            sys_log = SystemLog(
                level="ERROR",
                module="Celery:sync_customers_batch",
                message=f"Пакетная синхронизация ОСТАНОВЛЕНА: {str(e)}",
                stack_trace=error_details
            )
            session.add(sys_log)
            session.commit()
            
        logger.info("Синхронизация полностью остановлена до устранения причин ошибки.")
        raise e

@celery_app.task(bind=True, name="app.tasks.customer_tasks.import_customers_from_file_task")
def import_customers_from_file_task(self, file_path: str, status_id: int):
    """
    Задача для импорта клиентов из загруженного файла
    """
    try:
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "running"
                status.details = f"Парсинг файла {os.path.basename(file_path)}..."
                session.add(status)
                session.commit()

        # 1. Парсинг файла
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.xlsx':
            customers_data = import_service.parse_xlsx(file_path)
        elif ext == '.xml':
            customers_data = import_service.parse_xml(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
            
        total = len(customers_data)
        logger.info(f"Starting import of {total} customers from {file_path}")
        
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.total_count = total
                status.details = "Сохранение данных в базу..."
                session.add(status)
                session.commit()
        
        added = 0
        updated = 0
        chunk_size = 100
        
        # 2. Поэтапная обработка
        for i in range(0, total, chunk_size):
            # Проверка на паузу или отмену
            while True:
                with Session(engine) as session:
                    status = session.get(SyncStatus, status_id)
                    if not status or status.status == "cancelled":
                        logger.info(f"Import task {status_id} cancelled")
                        return "Cancelled"
                    if not status.is_paused:
                        break
                logger.info(f"Import task {status_id} is paused, waiting 10s...")
                time.sleep(10)
                
            chunk = customers_data[i:i + chunk_size]
            
            with Session(engine) as session:
                for c_data in chunk:
                    # Нормализация телефона при импорте
                    raw_phone = c_data.get('phone')
                    if not raw_phone: continue
                    
                    from app.utils.phone_utils import normalize_phone
                    clean_phone = normalize_phone(raw_phone)
                    
                    if not clean_phone: continue
                    
                    customer = session.exec(select(Customer).where(Customer.phone == clean_phone)).first()
                    
                    if not customer:
                        customer = Customer(phone=clean_phone)
                        added += 1
                    else:
                        updated += 1
                    
                    # Обновление полей
                    if c_data.get('name'): customer.name = c_data['name']
                    if c_data.get('surname'): customer.surname = c_data['surname']
                    if c_data.get('email'): customer.email = c_data['email']
                    if c_data.get('card_number'): customer.card_number = str(c_data['card_number'])
                    if c_data.get('gender'): customer.gender = c_data['gender']
                    
                    if 'is_marketing_consented' in c_data:
                        val = str(c_data['is_marketing_consented']).lower()
                        customer.is_marketing_consented = val in ['true', 'yes', '1', 'да', '+']
                    
                    if 'birthday' in c_data and c_data['birthday']:
                        try:
                            if isinstance(c_data['birthday'], datetime):
                                customer.birthday = c_data['birthday'].date()
                            else:
                                customer.birthday = datetime.fromisoformat(str(c_data['birthday'])).date()
                        except:
                            pass
                    
                    customer.updated_at = datetime.now(timezone.utc)
                    session.add(customer)
                
                # Обновление статуса после чанка
                status = session.get(SyncStatus, status_id)
                if status:
                    status.processed_count = min(i + chunk_size, total)
                    status.added_count = added
                    status.updated_count = updated
                    session.add(status)
                    session.commit()
        
        # 3. Завершение
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "completed"
                status.details = f"Импорт завершен. Добавлено: {added}, Обновлено: {updated}"
                status.updated_at = datetime.now(timezone.utc)
                session.add(status)
                
                # Логируем в системный лог
                sys_log = SystemLog(
                    level="INFO",
                    module="Celery:import_customers",
                    message=f"Импорт из файла завершен. Добавлено: {status.added_count}, Обновлено: {status.updated_count}",
                    stack_trace=None
                )
                session.add(sys_log)
                session.commit()
        
        # Удаляем временный файл
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return f"Import finished: {added} added, {updated} updated"
        
    except Exception as e:
        logger.error(f"Error importing customers: {e}")
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "error"
                status.details = str(e)
                session.add(status)
            
            # Логируем в системный лог
            sys_log = SystemLog(
                level="ERROR",
                module="Celery:import_customers",
                message=f"Ошибка импорта клиентов из файла: {str(e)}",
                stack_trace=None
            )
            session.add(sys_log)
            session.commit()
            
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e

@celery_app.task(name="app.tasks.customer_tasks.sync_single_customer_task")
def sync_single_customer_task(phone: str):
    """Задача для синхронизации одного клиента (вызывается при новом заказе)"""
    loop = asyncio.get_event_loop()
    with Session(engine) as session:
        loop.run_until_complete(_sync_single_customer(session, phone))
    return f"Synced {phone}"

@celery_app.task(name="app.tasks.customer_tasks.sync_guest_data_task")
def sync_guest_data_task(customer_id: int):
    """Задача для полной синхронизации по ID клиента"""
    loop = asyncio.get_event_loop()
    with Session(engine) as session:
        customer = session.get(Customer, customer_id)
        if customer and customer.phone:
            loop.run_until_complete(_sync_single_customer(session, customer.phone))
    return f"Synced customer {customer_id}"
