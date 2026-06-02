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
        settlement = addr.get("settlement", "") # iiko иногда отдает населенный пункт
        street = addr.get("street", "")
        house = addr.get("house", "")
        flat = addr.get("flat", "")
        entrance = addr.get("entrance", "")
        floor = addr.get("floor", "")
        doorphone = addr.get("doorphone", "") # домофон
        
        parts = []
        if city: parts.append(city)
        if settlement: parts.append(settlement)
        if street: 
            s_val = f"ул. {street}" if not any(k in street.lower() for k in ['ул.', 'пр.', 'б-р', 'пер.']) else street
            parts.append(s_val)
        if house: 
            h_val = f"д. {house}" if "д." not in house.lower() else house
            parts.append(h_val)
        if entrance: 
            en_val = f"под. {entrance}" if "под." not in entrance.lower() else entrance
            parts.append(en_val)
        if floor: 
            fl_val = f"эт. {floor}" if "эт." not in floor.lower() else floor
            parts.append(fl_val)
        if flat: 
            apt_val = f"кв. {flat}" if not any(k in flat.lower() for k in ['кв.', 'офис']) else flat
            parts.append(apt_val)
        if doorphone: 
            dp_val = f"дом. {doorphone}" if "дом." not in doorphone.lower() else doorphone
            parts.append(dp_val)
        
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
        
        street_normalized = street or ""
        city_normalized = city or "Тюмень"
        house_normalized = house or "-"
        settlement_normalized = settlement or ""

        # Ищем, есть ли уже такой адрес по компонентам
        existing_history = session.exec(
            select(ClientAddressHistory).where(
                ClientAddressHistory.client_id == customer_id,
                ClientAddressHistory.city == city_normalized,
                ClientAddressHistory.street == street_normalized,
                ClientAddressHistory.house == house_normalized
            )
        ).first()
        
        try:
            with session.begin_nested():
                if not existing_history:
                    new_history = ClientAddressHistory(
                        client_id=customer_id,
                        city=city_normalized,
                        settlement=settlement_normalized,
                        street=street_normalized,
                        house=house_normalized,
                        entrance=entrance or "",
                        floor=floor or "",
                        apartment=flat or "",
                        doorphone=doorphone or "",
                        address=full_address or "",
                        last_used_at=datetime.now(timezone.utc).replace(tzinfo=None),
                        orders_count=1
                    )
                    session.add(new_history)
                else:
                    existing_history.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    existing_history.orders_count += 1
                    existing_history.address = full_address
                    session.add(existing_history)
        except Exception as e:
            logger.warning(f"Failed to sync ClientAddressHistory for customer {customer_id}: {e}")

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

async def _sync_single_customer(session: Session, phone: str, organization_id: Optional[str] = None, order_id: Optional[int] = None, fast_sync: bool = False) -> bool:
    """Прокси для вызова синхронизации из iiko_sync_service"""
    from app.services.iiko_sync_service import iiko_sync_service
    return await iiko_sync_service.sync_single_customer(session, phone, organization_id, order_id, fast_sync=fast_sync)



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
                
                if loop.run_until_complete(_sync_single_customer(session, clean_phone, fast_sync=True)):
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
                        session.add(customer)
                        session.flush() # Получаем ID
                        added += 1
                    else:
                        updated += 1
                    
                    # Обновление основных полей
                    if c_data.get('name'):
                        customer.name = c_data['name']
                        customer.first_name = c_data['name']
                    if c_data.get('surname'):
                        customer.surname = c_data['surname']
                        customer.last_name = c_data['surname']
                    if c_data.get('email'): customer.email = c_data['email']
                    if c_data.get('card_number'): customer.card_number = str(c_data['card_number'])
                    if c_data.get('gender'): customer.gender = c_data['gender']
                    
                    # Новые поля из ТЗ
                    if c_data.get('registration_source'): customer.registration_source = c_data['registration_source']
                    if c_data.get('registration_date'):
                        try:
                            if isinstance(c_data['registration_date'], datetime):
                                customer.registration_date = c_data['registration_date']
                            else:
                                customer.registration_date = datetime.fromisoformat(str(c_data['registration_date']))
                        except: pass
                    
                    if 'is_high_risk' in c_data: customer.is_high_risk = bool(c_data['is_high_risk'])
                    if 'is_synced_to_iiko_cards' in c_data: customer.is_synced_to_iiko_cards = bool(c_data['is_synced_to_iiko_cards'])
                    
                    # Согласия на уведомления
                    if 'is_system_notifications_consented' in c_data: customer.is_system_notifications_consented = bool(c_data['is_system_notifications_consented'])
                    if 'is_loyalty_messages_consented' in c_data: customer.is_loyalty_messages_consented = bool(c_data['is_loyalty_messages_consented'])
                    if 'is_marketing_consented' in c_data: customer.is_marketing_consented = bool(c_data['is_marketing_consented'])
                    
                    if 'birthday' in c_data and c_data['birthday']:
                        try:
                            if isinstance(c_data['birthday'], datetime):
                                customer.birthday = c_data['birthday'].date()
                            else:
                                customer.birthday = datetime.fromisoformat(str(c_data['birthday'])).date()
                        except: pass

                    if c_data.get('last_order_date'):
                        try:
                            if isinstance(c_data['last_order_date'], datetime):
                                customer.last_order_date = c_data['last_order_date']
                            else:
                                customer.last_order_date = datetime.fromisoformat(str(c_data['last_order_date']))
                        except: pass
                    
                    customer.updated_at = datetime.now(timezone.utc)
                    session.add(customer)
                    
                    # Обработка дополнительных телефонов
                    if c_data.get('additional_phones'):
                        from app.models.customer import GuestPhone
                        for p_num in c_data['additional_phones']:
                            existing_p = session.exec(select(GuestPhone).where(
                                GuestPhone.customer_id == customer.id,
                                GuestPhone.phone == p_num
                            )).first()
                            if not existing_p:
                                session.add(GuestPhone(customer_id=customer.id, phone=p_num, comment="Импорт"))
                    
                    # Обработка адресов
                    all_addr = []
                    if c_data.get('address'): all_addr.append(c_data['address'])
                    if c_data.get('additional_addresses'): all_addr.extend(c_data['additional_addresses'])
                    
                    if all_addr:
                        from app.models.customer import GuestAddress, ClientAddressHistory
                        for addr_str in all_addr:
                            # GuestAddress
                            existing_ga = session.exec(select(GuestAddress).where(
                                GuestAddress.customer_id == customer.id,
                                GuestAddress.address == addr_str
                            )).first()
                            if not existing_ga:
                                session.add(GuestAddress(customer_id=customer.id, address=addr_str, is_main=(addr_str == all_addr[0])))
                            
                            # ClientAddressHistory (Laravel)
                            existing_cah = session.exec(select(ClientAddressHistory).where(
                                ClientAddressHistory.client_id == customer.id,
                                ClientAddressHistory.address == addr_str
                            )).first()
                            if not existing_cah:
                                # Более детальный парсинг адреса для заполнения обязательных полей Laravel
                                city, settlement, street, house, apartment, entrance, floor, doorphone = "Тюмень", None, "Не указана", "-", "", "", "", ""
                                try:
                                    # Пытаемся разбить по запятой
                                    parts = [p.strip() for p in addr_str.split(',')]
                                    # Пример: Тюмень, ул. Ленина, д. 1, под. 1, эт. 2, кв. 3
                                    for p in parts:
                                        p_low = p.lower()
                                        if any(k in p_low for k in ['тюмень', 'г.', 'город']): city = p
                                        elif any(k in p_low for k in ['ул.', 'пр-кт', 'проезд', 'бульвар']): street = p
                                        elif any(k in p_low for k in ['д.', 'дом']): house = p
                                        elif any(k in p_low for k in ['кв.', 'офис', 'квартира']): apartment = p
                                        elif any(k in p_low for k in ['под.', 'подъезд']): entrance = p
                                        elif any(k in p_low for k in ['эт.', 'этаж']): floor = p
                                        elif any(k in p_low for k in ['дом.', 'домофон']): doorphone = p
                                        elif not street and not any(k in p_low for k in ['д.', 'дом', 'под.', 'кв.']):
                                            # Если еще не нашли улицу и нет маркеров дома/подъезда - это может быть населенный пункт или улица
                                            if city and p != city: settlement = p
                                except: pass

                                try:
                                    with session.begin_nested():
                                        session.add(ClientAddressHistory(
                                            client_id=customer.id,
                                            city=city or "Тюмень",
                                            settlement=settlement or "",
                                            street=street or "",
                                            house=house or "-",
                                            entrance=entrance or "",
                                            floor=floor or "",
                                            apartment=apartment or "",
                                            doorphone=doorphone or "",
                                            address=addr_str or "",
                                            last_used_at=datetime.now(timezone.utc).replace(tzinfo=None),
                                            orders_count=1
                                        ))
                                except Exception as e:
                                    logger.warning(f"Failed to add ClientAddressHistory during import: {e}")
                
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
def sync_single_customer_task(phone: str, order_id: Optional[int] = None, fast_sync: bool = False):
    """Задача для синхронизации одного клиента (вызывается при новом заказе)"""
    loop = asyncio.get_event_loop()
    with Session(engine) as session:
        loop.run_until_complete(_sync_single_customer(session, phone, order_id=order_id, fast_sync=fast_sync))
    return f"Synced {phone} (Order: {order_id})"

@celery_app.task(name="app.tasks.customer_tasks.sync_guest_data_task")
def sync_guest_data_task(customer_id: int, fast_sync: bool = False):
    """Задача для полной синхронизации по ID клиента"""
    loop = asyncio.get_event_loop()
    with Session(engine) as session:
        customer = session.get(Customer, customer_id)
        if customer and customer.phone:
            loop.run_until_complete(_sync_single_customer(session, customer.phone, fast_sync=fast_sync))
    return f"Synced customer {customer_id}"

@celery_app.task(name="app.tasks.customer_tasks.export_customer_to_iiko_task")
def export_customer_to_iiko_task(customer_id: int):
    """
    Экспорт данных клиента из локальной БД в iiko Cloud.
    """
    loop = asyncio.get_event_loop()
    with Session(engine) as session:
        customer = session.get(Customer, customer_id)
        if not customer:
            logger.error(f"Export failed: Customer {customer_id} not found")
            return
            
        # Формируем payload для iiko
        birthday_str = None
        if customer.birthday:
            try:
                # birthday может быть как date так и datetime в модели
                from datetime import date, datetime
                if isinstance(customer.birthday, (date, datetime)):
                    dt = datetime.combine(customer.birthday, datetime.min.time()) if isinstance(customer.birthday, date) else customer.birthday
                    birthday_str = dt.strftime("%Y-%m-%d %H:%M:%S.000")
            except:
                pass
            
        sex = 0 # NotSpecified
        if customer.gender:
            g = str(customer.gender).lower()
            if g in ("male", "муж", "м", "1", "мужской"): sex = 1
            elif g in ("female", "жен", "ж", "2", "женский"): sex = 2
            
        customer_data = {
            "phone": customer.phone,
            "name": customer.first_name or customer.name or "",
            "surName": customer.last_name or customer.surname or "",
            "middleName": customer.middle_name,
            "email": customer.email,
            "birthday": birthday_str,
            "sex": sex,
            "shouldBeCheckedForRisk": bool(customer.is_high_risk),
            "isHighRisk": bool(customer.is_high_risk),
            "checkedForRisk": bool(customer.is_high_risk),
            "referrerId": customer.referrer,
            "userData": customer.notes or customer.iiko_notes
        }
        
        # Очищаем от пустых значений и None, но оставляем обязательные
        customer_data = {k: v for k, v in customer_data.items() if v is not None}
        
        # Если есть iiko_id, используем его для однозначной идентификации
        if customer.iiko_id:
            customer_data["id"] = customer.iiko_id
            
        try:
            # Вызываем сервис iiko для обновления профиля
            result = loop.run_until_complete(iiko_service.create_or_update_customer(customer_data))
            logger.info(f"Customer {customer.phone} successfully exported to iiko. Result ID: {result.get('id')}")
            
            # 2. Синхронизация категорий
            try:
                # Получаем текущую инфу о госте из iiko
                iiko_info = loop.run_until_complete(iiko_service.get_customer_info(customer.phone))
                if iiko_info and iiko_info.get("id"):
                    iiko_cust_id = iiko_info["id"]
                    
                    # Текущие категории в iiko (имена)
                    current_iiko_cat_names = []
                    if "categories" in iiko_info:
                        current_iiko_cat_names = [c["name"] for c in iiko_info["categories"] if isinstance(c, dict) and c.get("name")]
                    
                    # Категории, которые должны быть (из нашей БД)
                    target_cat_names = customer.iiko_categories or []
                    
                    # Если есть расхождения - синхронизируем
                    if set(current_iiko_cat_names) != set(target_cat_names):
                        logger.info(f"Syncing categories for {customer.phone}. Current: {current_iiko_cat_names}, Target: {target_cat_names}")
                        
                        # Нам нужны ID категорий
                        all_cats_data = loop.run_until_complete(iiko_service.get_customer_categories())
                        all_cats = all_cats_data.get("guestCategories", [])
                        name_to_id = {c["name"]: c["id"] for c in all_cats if c.get("name") and c.get("id")}
                        
                        # Категории для добавления
                        for name in target_cat_names:
                            if name not in current_iiko_cat_names and name in name_to_id:
                                loop.run_until_complete(iiko_service.add_customer_category(iiko_cust_id, name_to_id[name]))
                                logger.info(f"Added category '{name}' to {customer.phone}")
                                
                        # Категории для удаления
                        for name in current_iiko_cat_names:
                            if name not in target_cat_names and name in name_to_id:
                                loop.run_until_complete(iiko_service.remove_customer_category(iiko_cust_id, name_to_id[name]))
                                logger.info(f"Removed category '{name}' from {customer.phone}")
            except Exception as cat_err:
                logger.error(f"Failed to sync categories for customer {customer.phone}: {cat_err}")

            # После успешного экспорта запускаем синхронизацию обратно, чтобы обновить все поля
            # (так как iiko может изменить ID или добавить какие-то данные)
            sync_single_customer_task.delay(customer.phone)
            
        except Exception as e:
            logger.error(f"Failed to export customer {customer.phone} to iiko: {e}")
