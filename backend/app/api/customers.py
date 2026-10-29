"""
API эндпоинты для управления Клиентами
"""
from typing import List, Optional, Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlmodel import Session, select, func, or_
from app.core.database import get_session
from app.models.customer import Customer, BonusTransaction, GuestAddress, GuestPhone
from app.models.order import Order
from app.models.vk_bot import VkBotAccount
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerPaginationResponse
from app.utils.phone_utils import normalize_phone, format_phone_iiko
import json
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
import logging
import shutil
import os
from app.services.iiko_service import iiko_service
from app.models.sync_log import SyncStatus
from app.tasks.customer_tasks import sync_customers_batch, import_customers_from_file_task, sync_single_customer_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("/", response_model=CustomerPaginationResponse)
def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100000),
    search: Optional[str] = None,
    categories: Optional[List[str]] = Query(None),
    filter_duplicates_phone: bool = Query(False),
    filter_duplicates_uid: bool = Query(False),
    social_channel: Optional[str] = Query(None),
    sort_social: bool = Query(False),
    session: Session = Depends(get_session)
):
    """Список клиентов с пагинацией и расширенным поиском"""
    from app.models.vk_user import VkUser
    from app.models.max_settings import MaxSettings
    from sqlalchemy import case, Integer
    
    skip = (page - 1) * limit
    
    # Базовый запрос
    query = select(Customer)
    count_query = select(func.count()).select_from(Customer)
    
    if filter_duplicates_phone:
        subquery = select(Customer.phone).group_by(Customer.phone).having(func.count(Customer.phone) > 1)
        query = query.where(Customer.phone.in_(subquery))
        count_query = count_query.where(Customer.phone.in_(subquery))
        
    if filter_duplicates_uid:
        subquery = select(Customer.uid).where(Customer.uid != None, Customer.uid != "").group_by(Customer.uid).having(func.count(Customer.uid) > 1)
        query = query.where(Customer.uid.in_(subquery))
        count_query = count_query.where(Customer.uid.in_(subquery))

    if search:
        search_filter = or_(
            Customer.phone.ilike(f"%{search}%"),
            Customer.name.ilike(f"%{search}%"),
            Customer.surname.ilike(f"%{search}%"),
            Customer.notes.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
        
    if categories and len(categories) > 0:
        # Фильтруем по каждой категории через OR
        category_filters = []
        for cat in categories:
            # Ищем категорию внутри JSON строки: "CategoryName"
            category_filters.append(Customer.loyalty_categories.ilike(f'%"{cat}"%'))
            # Также проверяем старое поле на всякий случай
            category_filters.append(Customer.categories.ilike(f'%"{cat}"%'))
            
        if category_filters:
            query = query.where(or_(*category_filters))
            count_query = count_query.where(or_(*category_filters))
            
    # Фильтрация по каналам связи
    if social_channel:
        if social_channel == "vk":
            vk_subquery = select(VkUser.phone).where(VkUser.is_linked == True)
            query = query.where(or_(Customer.vk_user_id != None, Customer.phone.in_(vk_subquery)))
            count_query = count_query.where(or_(Customer.vk_user_id != None, Customer.phone.in_(vk_subquery)))
        elif social_channel == "telegram":
            query = query.where(Customer.telegram_id != None)
            count_query = count_query.where(Customer.telegram_id != None)
        elif social_channel in ("whatsapp", "max"):
            # Для WhatsApp/MAX считаем по согласию гостя на уведомления
            query = query.where(Customer.is_system_notifications_consented == True).where(Customer.is_blocked == False)
            count_query = count_query.where(Customer.is_system_notifications_consented == True).where(Customer.is_blocked == False)
        elif social_channel == "sms":
            # Только телефон (нет VK и TG)
            query = query.where(Customer.vk_user_id == None).where(Customer.telegram_id == None)
            count_query = count_query.where(Customer.vk_user_id == None).where(Customer.telegram_id == None)
        
    # Сортировка
    if sort_social:
        sort_expr = case(
            (Customer.vk_user_id != None, 1),
            else_=0
        ) + case(
            (Customer.telegram_id != None, 1),
            else_=0
        )
        query = query.order_by(sort_expr.desc(), Customer.created_at.desc())
    else:
        query = query.order_by(Customer.created_at.desc())
        
    # Пагинация
    query = query.offset(skip).limit(limit)
    
    # Выполнение запросов
    total = session.exec(count_query).one()
    customers = session.exec(query).all()
    
    # Обогащение социальными сетями
    max_settings = session.exec(select(MaxSettings)).first()
    has_whatsapp_bot = False
    has_max_bot = False
    if max_settings and max_settings.is_active:
        for bot in max_settings.bots:
            if bot.is_active:
                if bot.bot_type.lower() == "whatsapp":
                    has_whatsapp_bot = True
                elif bot.bot_type.lower() == "max":
                    has_max_bot = True
                    
    phones = [c.phone for c in customers if c.phone]
    vk_ids = [c.vk_user_id for c in customers if c.vk_user_id]
    
    vk_users = []
    if phones or vk_ids:
        vk_users_query = select(VkUser)
        filters = []
        if phones:
            filters.append(VkUser.phone.in_(phones))
        if vk_ids:
            filters.append(VkUser.vk_id.in_(vk_ids))
        vk_users = session.exec(vk_users_query.where(or_(*filters))).all()
        
    vk_user_by_phone = {u.phone: u for u in vk_users if u.phone}
    vk_user_by_vk_id = {u.vk_id: u for u in vk_users}
    
    response_items = []
    for c in customers:
        channels = {}
        
        # 1. VK
        vk_user = vk_user_by_vk_id.get(c.vk_user_id) if c.vk_user_id else None
        if not vk_user and c.phone:
            vk_user = vk_user_by_phone.get(c.phone)
            
        if vk_user:
            channels["vk"] = {
                "connected": True,
                "active": bool(vk_user.is_subscribed and vk_user.notifications_enabled and not vk_user.is_blocked),
                "blocked": bool(vk_user.is_blocked or not vk_user.notifications_enabled or not vk_user.is_subscribed)
            }
        else:
            channels["vk"] = {
                "connected": False,
                "active": False,
                "blocked": False
            }
            
        # 2. Telegram
        if c.telegram_id:
            is_active = bool(c.is_system_notifications_consented and not c.is_blocked)
            channels["telegram"] = {
                "connected": True,
                "active": is_active,
                "blocked": not is_active
            }
        else:
            channels["telegram"] = {
                "connected": False,
                "active": False,
                "blocked": False
            }
            
        # 3. WhatsApp
        if has_whatsapp_bot and c.phone:
            is_active = bool(c.is_system_notifications_consented and not c.is_blocked)
            channels["whatsapp"] = {
                "connected": True,
                "active": is_active,
                "blocked": not is_active
            }
        else:
            channels["whatsapp"] = {
                "connected": False,
                "active": False,
                "blocked": False
            }
            
        # 4. MAX
        if has_max_bot and c.phone:
            is_active = bool(c.is_system_notifications_consented and not c.is_blocked)
            channels["max"] = {
                "connected": True,
                "active": is_active,
                "blocked": not is_active
            }
        else:
            channels["max"] = {
                "connected": False,
                "active": False,
                "blocked": False
            }
            
        # 5. SMS (если нет VK и TG)
        if c.phone and not channels["vk"]["connected"] and not channels["telegram"]["connected"]:
            is_active = bool(c.is_system_notifications_consented and not c.is_blocked)
            channels["sms"] = {
                "connected": True,
                "active": is_active,
                "blocked": not is_active
            }
        else:
            channels["sms"] = {
                "connected": False,
                "active": False,
                "blocked": False
            }
            
        res_customer = CustomerResponse.model_validate(c)
        res_customer.social_channels = channels
        response_items.append(res_customer)
    
    return {
        "items": response_items,
        "total": total
    }

@router.get("/categories-list")
def get_categories_list(session: Session = Depends(get_session)):
    """Получить список всех уникальных категорий из БД"""
    # Получаем все непустые loyalty_categories
    results = session.exec(
        select(Customer.loyalty_categories)
        .where(Customer.loyalty_categories != None)
        .where(Customer.loyalty_categories != '[]')
    ).all()
    
    unique_categories = set()
    for res in results:
        try:
            cats = json.loads(res)
            if isinstance(cats, list):
                for c in cats:
                    if isinstance(c, str):
                        unique_categories.add(c)
                    elif isinstance(c, dict) and c.get("name"):
                        unique_categories.add(c["name"])
        except Exception:
            # Если это просто строка через запятую
            if res:
                for c in res.split(','):
                    unique_categories.add(c.strip())
                    
    return sorted(list(unique_categories))
    
@router.get("/all-iiko-categories")
async def get_all_iiko_categories():
    """Получить полный список категорий из iiko Cloud"""
    try:
        categories_data = await iiko_service.get_customer_categories()
        # В iiko Cloud ответ содержит {"guestCategories": [{"id": "...", "name": "..."}, ...]}
        return categories_data.get("guestCategories", [])
    except Exception as e:
        logger.error(f"Error fetching categories from iiko: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, session: Session = Depends(get_session)):
    """Детали одного клиента (и запуск фонового обновления)"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    
    # Автозамена пустого/placeholder имени из связанного VK-профиля
    name_val = customer.name.strip() if customer.name else ""
    if not name_val or name_val.lower() in ("не задано", "гость"):
        from app.models.vk_user import VkUser
        vk_user = session.exec(
            select(VkUser)
            .where((VkUser.phone == customer.phone) | (VkUser.vk_id == customer.vk_user_id))
            .where(VkUser.is_linked == True)
        ).first()
        
        if vk_user and (vk_user.first_name or vk_user.last_name):
            new_name = vk_user.first_name or "Гость"
            new_surname = vk_user.last_name or ""
            
            customer.name = new_name
            customer.first_name = new_name
            customer.surname = new_surname
            customer.last_name = new_surname
            customer.updated_at = datetime.now(timezone.utc)
            
            session.add(customer)
            session.commit()
            session.refresh(customer)
            logger.info(f"Synchronously updated customer {customer.phone} placeholder name to '{new_name} {new_surname}' from VK user")
            
    # Запускаем фоновую синхронизацию, чтобы при следующем просмотре или обновлении страницы данные были свежими
    try:
        sync_single_customer_task.delay(customer.phone)
    except Exception as e:
        logger.warning(f"Failed to trigger auto-sync for customer {customer.phone}: {e}")
    
    # [FIX] Наполняем детальные адреса из истории
    # Теперь мы возвращаем СПИСОК ОБЪЕКТОВ, а не просто строк, чтобы фронтенд мог вывести детали
    detailed_addresses = []
    
    def format_detailed_address(addr_obj):
        parts = []
        if getattr(addr_obj, 'city', None): parts.append(addr_obj.city)
        if getattr(addr_obj, 'settlement', None): parts.append(addr_obj.settlement)
        if getattr(addr_obj, 'street', None): 
            s = addr_obj.street
            parts.append(f"ул. {s}" if not any(k in s.lower() for k in ['ул.', 'пр.', 'б-р', 'пер.']) else s)
        if getattr(addr_obj, 'house', None): 
            h = addr_obj.house
            parts.append(f"д. {h}" if "д." not in h.lower() else h)
        if getattr(addr_obj, 'entrance', None): 
            e = addr_obj.entrance
            parts.append(f"под. {e}" if "под." not in e.lower() else e)
        if getattr(addr_obj, 'floor', None): 
            fl = addr_obj.floor
            parts.append(f"эт. {fl}" if "эт." not in fl.lower() else fl)
        if getattr(addr_obj, 'apartment', None) or getattr(addr_obj, 'flat', None): 
            apt = getattr(addr_obj, 'apartment', None) or getattr(addr_obj, 'flat', None)
            parts.append(f"кв. {apt}" if not any(k in apt.lower() for k in ['кв.', 'офис']) else apt)
        if getattr(addr_obj, 'doorphone', None): 
            dp = addr_obj.doorphone
            parts.append(f"дом. {dp}" if "дом." not in dp.lower() else dp)
        return ", ".join(parts)

    # 1. Берем из ClientAddressHistory (Laravel формат)
    if customer.addresses_history:
        for addr in customer.addresses_history:
            detailed_addresses.append({
                "id": addr.id,
                "city": addr.city or "Тюмень",
                "settlement": addr.settlement,
                "street": addr.street,
                "house": addr.house,
                "entrance": addr.entrance,
                "floor": addr.floor,
                "apartment": addr.apartment,
                "doorphone": addr.doorphone,
                "address": addr.address or format_detailed_address(addr)
            })
            
    # 2. Если история пуста, пробуем взять из GuestAddress (Legacy формат)
    if not detailed_addresses and customer.guest_addresses:
        for ga in customer.guest_addresses:
            detailed_addresses.append({
                "id": ga.id,
                "address": ga.address,
                "city": "Тюмень",
                "street": "Не указана"
            })

    # Создаем объект ответа на основе схемы
    # Так как мы используем response_model=CustomerResponse, FastAPI автоматически 
    # преобразует этот объект в нужный формат. Нам достаточно передать объект с нужным полем.
    customer.addresses = detailed_addresses
    return customer
    
@router.get("/by-phone/{phone}", response_model=CustomerResponse)
async def get_customer_by_phone(phone: str, session: Session = Depends(get_session)):
    """Получить данные клиента по номеру телефона (с нормализацией)"""
    normalized = normalize_phone(phone)
    customer = session.exec(select(Customer).where(Customer.phone == normalized)).first()
    if not customer:
        # Если клиент не найден локально, пытаемся синхронизировать его из iiko
        from app.services.iiko_sync_service import iiko_sync_service
        try:
            # Используем нормализованный телефон или исходный
            search_phone = normalized if normalized else phone
            await iiko_sync_service.sync_single_customer(session, search_phone)
            
            # Повторный поиск после синхронизации
            customer = session.exec(select(Customer).where(Customer.phone == search_phone)).first()
            if not customer and normalized:
                # Если нормализация iiko отличается от нашей, пробуем поискать еще раз
                customer = session.exec(select(Customer).where(Customer.phone == search_phone)).first()
        except Exception as e:
            logger.warning(f"Auto-sync failed for phone {phone} during lookup: {e}")

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Запускаем фоновую синхронизацию для актуализации данных
    try:
        sync_single_customer_task.delay(customer.phone)
    except Exception as e:
        logger.warning(f"Failed to trigger auto-sync for customer {customer.phone}: {e}")
        
    return customer

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: CustomerCreate,
    session: Session = Depends(get_session)
):
    """Создать профиль клиента"""
    # Нормализуем телефон перед поиском и сохранением
    customer_data.phone = normalize_phone(customer_data.phone)
    
    existing = session.exec(select(Customer).where(Customer.phone == customer_data.phone)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Customer with this phone already exists")
        
    customer = Customer(**customer_data.model_dump())
    session.add(customer)
    session.commit()
    session.refresh(customer)

    # Фоновый поиск и привязка аккаунта MAX
    if customer.phone and not customer.max_user_id:
        try:
            from app.tasks.customer_tasks import link_customer_max_task
            link_customer_max_task.delay(customer.id)
        except Exception as e:
            logger.warning(f"Could not queue link_customer_max_task for customer #{customer.id}: {e}")

    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    session: Session = Depends(get_session)
):
    """Обновление профиля клиента"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_data.model_dump(exclude_unset=True)
    if "phone" in update_data:
        update_data["phone"] = normalize_phone(update_data["phone"])
        
    # Синхронизируем поля имен
    if "name" in update_data and "first_name" not in update_data:
        update_data["first_name"] = update_data["name"]
    elif "first_name" in update_data and "name" not in update_data:
        update_data["name"] = update_data["first_name"]
        
    if "surname" in update_data and "last_name" not in update_data:
        update_data["last_name"] = update_data["surname"]
    elif "last_name" in update_data and "surname" not in update_data:
        update_data["surname"] = update_data["last_name"]

    # Convert empty strings to None for fields that should be NULL in DB
    for key in ["birthday", "middle_name", "referrer", "registration_source", "registered_organization", "risk_reason", "iiko_notes"]:
        if key in update_data and update_data[key] == "":
            update_data[key] = None

    for key, value in update_data.items():
        if hasattr(customer, key):
            setattr(customer, key, value)

    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    # Запускаем фоновую синхронизацию (выгрузка в iiko Cloud)
    try:
        from app.tasks.customer_tasks import export_customer_to_iiko_task
        export_customer_to_iiko_task.delay(customer.id)
    except Exception as e:
        logger.warning(f"Failed to trigger export after update for {customer.phone}: {e}")

    # Если телефон есть, но max_user_id не привязан — запускаем поиск в MAX
    if customer.phone and not customer.max_user_id:
        try:
            from app.tasks.customer_tasks import link_customer_max_task
            link_customer_max_task.delay(customer.id)
        except Exception as e:
            logger.warning(f"Could not queue link_customer_max_task for customer #{customer.id}: {e}")
        
    return customer

@router.post("/{customer_id}/link-max")
async def link_customer_max_endpoint(customer_id: int, session: Session = Depends(get_session)):
    """Поиск и привязка аккаунта MAX для конкретного клиента по номеру телефона"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not customer.phone:
        raise HTTPException(status_code=400, detail="Customer phone is empty")
    from app.services.max_bridge_service import max_bridge_service
    res = await max_bridge_service.search_user_by_phone(customer.phone, session)
    if res.get("found") and res.get("user_id"):
        customer.max_user_id = str(res["user_id"])
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return {"success": True, "max_user_id": customer.max_user_id, "data": res}
    return {"success": False, "error": res.get("error", "Пользователь не найден в MAX")}


@router.post("/{customer_id}/sync", response_model=CustomerResponse)
async def sync_customer(customer_id: int, session: Session = Depends(get_session)):
    """Синхронизация данных клиента с iiko Loyalty Server"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    try:
        from app.services.iiko_sync_service import iiko_sync_service
        await iiko_sync_service.sync_single_customer(session, customer.phone, bypass_cache=True)
        session.refresh(customer)
        return customer
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/{customer_id}/full-sync")
def full_sync_customer(customer_id: int, session: Session = Depends(get_session)):
    """Запуск полной фоновой синхронизации (профиль + OLAP + история) через Celery"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        from app.tasks.customer_tasks import sync_guest_data_task
        task = sync_guest_data_task.delay(customer.id)
        return {"status": "success", "task_id": task.id, "message": "Full sync task started"}
    except Exception as e:
        logger.error(f"Failed to trigger full-sync for customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync task: {str(e)}")

@router.get("/{customer_id}/bonus-history")
async def get_customer_bonus_history(
    customer_id: int, 
    date_from: str = Query(..., description="ГГГГ-ММ-ДД"),
    session: Session = Depends(get_session)
):
    """Получение истории бонусов клиента из iiko"""
    customer = session.get(Customer, customer_id)
    if not customer or not customer.iiko_customer_id:
        raise HTTPException(status_code=404, detail="Customer or iiko ID not found")
        
    try:
        history = await iiko_service.get_customer_bonus_history(
            customer.iiko_customer_id, 
            date_from
        )
        return history
    except Exception as e:
        logger.error(f"API Error fetching bonus history for customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch bonus history: {str(e)}")

@router.get("/{customer_id}/local-bonus-history")
def get_local_bonus_history(
    customer_id: int,
    session: Session = Depends(get_session)
):
    """Получение локальной истории бонусов из БД (накопленная информация)"""
    history = session.exec(
        select(BonusTransaction)
        .where(BonusTransaction.customer_id == customer_id)
        .order_by(BonusTransaction.transaction_date.desc())
        .limit(100)
    ).all()
    return {"transactions": history}
    




@router.get("/{customer_id}/local-addresses")
def get_local_addresses(
    customer_id: int,
    session: Session = Depends(get_session)
):
    """Получение локального списка адресов гостя"""
    addresses = session.exec(
        select(GuestAddress)
        .where(GuestAddress.customer_id == customer_id)
        .order_by(GuestAddress.created_at.desc())
    ).all()
    return {"addresses": addresses}

@router.get("/{customer_id}/local-phones")
def get_local_phones(
    customer_id: int,
    session: Session = Depends(get_session)
):
    """Получение локального списка дополнительных телефонов гостя"""
    phones = session.exec(
        select(GuestPhone)
        .where(GuestPhone.customer_id == customer_id)
        .order_by(GuestPhone.created_at.desc())
    ).all()
    return {"phones": phones}

@router.post("/{customer_id}/local-phones")
def add_local_phone(
    customer_id: int,
    phone_data: Dict[str, str],
    session: Session = Depends(get_session)
):
    """Добавление дополнительного телефона гостя"""
    phone = phone_data.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Номер телефона обязателен")
    
    normalized = normalize_phone(phone)
    
    # Проверка на дубликат у этого же клиента
    existing = session.exec(
        select(GuestPhone).where(
            GuestPhone.customer_id == customer_id,
            GuestPhone.phone == normalized
        )
    ).first()
    
    if existing:
        return {"status": "exists", "phone": existing}
    
    new_phone = GuestPhone(
        customer_id=customer_id,
        phone=normalized,
        is_active=True
    )
    session.add(new_phone)
    session.commit()
    session.refresh(new_phone)
    
    # Опционально: запуск синхронизации если нужно обновить iiko (но доп телефоны iiko пока не всегда умеет принимать пачкой)
    
    return {"status": "success", "phone": new_phone}

@router.delete("/{customer_id}/local-phones/{phone_id}")
def delete_local_phone(
    customer_id: int,
    phone_id: int,
    session: Session = Depends(get_session)
):
    """Удаление дополнительного телефона гостя"""
    phone = session.get(GuestPhone, phone_id)
    if not phone or phone.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Телефон не найден")
    
    session.delete(phone)
    session.commit()
    return {"status": "success"}

@router.post("/import")
def import_customers(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """Импорт клиентов из XLSX или XML файла"""
    try:
        # 1. Проверка расширения
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.xlsx', '.xml']:
            logger.warning(f"Unsupported file extension: {ext} for file {file.filename}")
            raise HTTPException(status_code=400, detail="Поддерживаются только файлы .xlsx и .xml")
        
        # 2. Сохранение во временный файл
        temp_dir = "temp_imports"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{datetime.now().timestamp()}_{file.filename}")
        
        logger.info(f"Saving uploaded file to {file_path}")
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_size = os.path.getsize(file_path)
            logger.info(f"File saved successfully. Size: {file_size} bytes")
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла на сервере: {str(e)}")
        
        # 3. Создание статуса
        sync_status = SyncStatus(
            task_id="pending",
            sync_type="import",
            total_count=0,
            processed_count=0,
            added_count=0,
            updated_count=0,
            status="running"
        )
        session.add(sync_status)
        session.commit()
        session.refresh(sync_status)
        
        # 4. Запуск задачи Celery
        try:
            task = import_customers_from_file_task.apply_async(args=[os.path.abspath(file_path), sync_status.id])
            sync_status.task_id = task.id
            session.add(sync_status)
            session.commit()
            
            logger.info(f"Import task started: {task.id}")
        except Exception as e:
            logger.error(f"Failed to start Celery task: {e}")
            sync_status.status = "error"
            sync_status.details = f"Failed to start background task: {str(e)}"
            session.add(sync_status)
            session.commit()
            raise HTTPException(status_code=500, detail=f"Не удалось запустить фоновую задачу: {str(e)}")
        
        return {
            "status": "success",
            "sync_id": sync_status.id,
            "task_id": task.id,
            "message": "Задача импорта запущена"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in import_customers: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера при импорте: {str(e)}")

@router.post("/sync-all")
def sync_all_customers(
    force_update: bool = Query(False, description="Принудительно обновить данные существующих клиентов"),
    session: Session = Depends(get_session)
):
    """
    Массовая синхронизация клиентов из iiko Cloud (через Celery).
    Запускает рекурсивную задачу по 50 человек с паузой.
    """
    sync_status = SyncStatus(
        task_id="pending",
        sync_type="customers",
        total_count=0,
        processed_count=0,
        added_count=0,
        updated_count=0,
        status="running"
    )
    session.add(sync_status)
    session.commit()
    session.refresh(sync_status)
    
    # Передаем force_update в задачу
    task = sync_customers_batch.apply_async(args=[0, sync_status.id, force_update])
    
    sync_status.task_id = task.id
    session.add(sync_status)
    session.commit()
    
    return {
        "status": "success", 
        "message": "Recursive customer sync task started",
        "sync_id": sync_status.id,
        "task_id": task.id
    }


@router.get("/sync-status/{sync_id}")
def get_sync_status(sync_id: int, session: Session = Depends(get_session)):
    """Получение прогресса синхронизации"""
    status = session.get(SyncStatus, sync_id)
    if not status:
        raise HTTPException(status_code=404, detail="Sync status not found")
    return status

@router.get("/sync-latest")
def get_latest_sync_status(session: Session = Depends(get_session)):
    """Получение статуса последней запущенной синхронизации"""
    status = session.exec(
        select(SyncStatus).where(SyncStatus.sync_type == "customers").order_by(SyncStatus.updated_at.desc())
    ).first()
    return status

@router.patch("/{customer_id}/iiko")
async def update_customer_in_iiko(
    customer_id: int,
    customer_data: dict,
    session: Session = Depends(get_session)
):
    """Обновление данных клиента в iiko Cloud"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    try:
        # Формируем payload для iiko Cloud
        # iiko требует чтобы был либо id, либо phone
        iiko_payload = {}
        
        if customer.iiko_customer_id and str(customer.iiko_customer_id).strip():
            iiko_payload["id"] = str(customer.iiko_customer_id).strip()
            
        if customer.phone:
            iiko_payload["phone"] = format_phone_iiko(customer.phone)
            
        # Данные для обновления
        if "name" in customer_data and customer_data["name"]:
            iiko_payload["name"] = customer_data["name"]
        elif customer.name:
            iiko_payload["name"] = customer.name
        
        email = customer_data.get("email", customer.email)
        if email:
            iiko_payload["email"] = email
            
        comment = customer_data.get("notes", customer.notes)
        if comment:
            iiko_payload["comment"] = comment
            
        birthday = customer_data.get("birthday")
        if birthday:
            # Преобразуем дату в формат iiko (yyyy-MM-dd HH:mm:ss.fff)
            if isinstance(birthday, str) and 'T' in birthday:
                birthday = birthday.split('T')[0]
            if isinstance(birthday, str):
                iiko_payload["birthday"] = f"{birthday} 00:00:00.000"

        # Новые поля для анкеты
        middle_name = customer_data.get("middle_name", customer.middle_name)
        if middle_name:
            iiko_payload["middleName"] = middle_name
            
        gender = customer_data.get("gender", customer.gender)
        if gender == "Мужской":
            iiko_payload["sex"] = 1
        elif gender == "Женский":
            iiko_payload["sex"] = 2
        else:
            iiko_payload["sex"] = 0

        referrer = customer_data.get("referrer", customer.referrer)
        if referrer:
            iiko_payload["referrerId"] = referrer

        # Синхронизация статуса риска (отправляем оба варианта поля для совместимости)
        is_high_risk = customer_data.get("is_high_risk")
        if is_high_risk is None:
            is_high_risk = customer.is_high_risk
            
        is_high_risk_val = bool(is_high_risk)
        iiko_payload["shouldBeCheckedForRisk"] = is_high_risk_val
        iiko_payload["isHighRisk"] = is_high_risk_val
        iiko_payload["checkedForRisk"] = is_high_risk_val
            
        # Удаляем None и пустые значения
        iiko_payload = {k: v for k, v in iiko_payload.items() if v is not None and str(v).strip() != ""}
        
        logger.info(f"Updating customer {customer_id} in iiko with payload: {iiko_payload}")
        
        result = await iiko_service.create_or_update_customer(iiko_payload)
        
        # В ответе iiko может быть id или вложенный объект customer
        res_id = result.get("id") or result.get("customer", {}).get("id")
        
        if res_id:
            # 1. Сначала обновляем локально основные данные
            for key, value in customer_data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            
            customer.updated_at = datetime.now(timezone.utc)
            session.add(customer)
            session.commit()
            session.refresh(customer)

            # 2. Логика автоматической генерации карты лояльности
            try:
                # Получаем полную информацию о клиенте из iiko, чтобы проверить карты и дату регистрации
                iiko_info = await iiko_service.get_customer_info(customer_id=res_id)
                
                # Условия: есть id, есть карты (проверяем на пустоту)
                # По спецификации iiko дата регистрации может не приходить в явном виде, 
                # поэтому ориентируемся на наличие id и отсутствие карт.
                cards = iiko_info.get("cards", [])
                
                if not cards:
                    logger.info(f"Customer {customer.phone} has no loyalty cards in iiko. Generating a new one...")
                    
                    # Генерация номера карты по маске: 72 + последние 10 цифр телефона
                    clean_phone = ''.join(filter(str.isdigit, customer.phone))
                    if len(clean_phone) >= 10:
                        last_10 = clean_phone[-10:]
                        new_card_number = f"72{last_10}"
                        
                        logger.info(f"Assigning new card {new_card_number} to customer {customer.phone}")
                        
                        # Отправляем запрос на добавление карты
                        card_payload = {
                            "organizationId": iiko_payload.get("organizationId"),
                            "id": res_id,
                            "phone": customer.phone,
                            "cardNumber": new_card_number,
                            "cardTrack": new_card_number
                        }
                        
                        card_res = await iiko_service.create_or_update_customer(card_payload)
                        if card_res.get("id") or card_res.get("customer", {}).get("id"):
                            logger.info(f"Successfully assigned card {new_card_number} to customer {customer.phone}")
                            customer.card_number = new_card_number
                            session.add(customer)
                            session.commit()
                        else:
                            logger.warning(f"Failed to assign card to customer {customer.phone}: {card_res}")
                    else:
                        logger.warning(f"Phone number {customer.phone} is too short to generate card number")

            except Exception as e:
                logger.error(f"Error during automatic card generation for {customer.phone}: {str(e)}")

            # 3. Запускаем фоновую синхронизацию для обновления всех остальных полей из iiko
            try:
                sync_single_customer_task.delay(customer.phone)
            except Exception as e:
                logger.warning(f"Failed to trigger sync after iiko update for {customer.phone}: {e}")
            
        return result
    except Exception as e:
        logger.error(f"iiko update failed for customer {customer_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"iiko update failed: {str(e)}")

@router.get("/{customer_id}/vk-account")
def get_customer_vk_account(customer_id: int, session: Session = Depends(get_session)):
    """Получение связанного VK аккаунта клиента"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.vk_user_id:
        return None
        
    vk_account = session.exec(select(VkBotAccount).where(VkBotAccount.vk_user_id == customer.vk_user_id)).first()
    return vk_account

@router.post("/{customer_id}/vk-link")
def link_customer_vk(
    customer_id: int, 
    vk_user_id: int, 
    session: Session = Depends(get_session)
):
    """Привязка VK ID к клиенту"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.vk_user_id = vk_user_id
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return {"status": "success", "vk_user_id": vk_user_id}


@router.get("/{customer_id}/social-accounts")
def get_customer_social_accounts(customer_id: int, session: Session = Depends(get_session)):
    """Получение связанных аккаунтов социальных сетей гостя"""
    from app.models.vk_user import VkUser
    
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    social_accounts = []
    
    # Ищем ВКонтакте аккаунт
    vk_user = None
    if customer.vk_user_id:
        vk_user = session.exec(select(VkUser).where(VkUser.vk_id == customer.vk_user_id)).first()
    elif customer.phone:
        vk_user = session.exec(select(VkUser).where(VkUser.phone == customer.phone)).first()
        
    if vk_user:
        social_accounts.append({
            "provider": "vk",
            "vk_id": vk_user.vk_id,
            "first_name": vk_user.first_name,
            "last_name": vk_user.last_name,
            "photo_50": vk_user.photo_50,
            "screen_name": vk_user.screen_name,
            "is_subscribed": vk_user.is_subscribed,
            "notifications_enabled": vk_user.notifications_enabled,
            "is_blocked": vk_user.is_blocked,
            "linked_at": vk_user.linked_at
        })
        
    # Ищем Telegram аккаунт
    if customer.telegram_id:
        social_accounts.append({
            "provider": "telegram",
            "telegram_id": customer.telegram_id,
            "first_name": customer.first_name or customer.name or "Telegram User",
            "last_name": customer.last_name or customer.surname or "",
            "photo_50": None,
            "screen_name": None,
            "is_subscribed": True,
            "notifications_enabled": customer.is_system_notifications_consented,
            "is_blocked": customer.is_blocked,
            "linked_at": None
        })
        
    # Ищем MAX аккаунт
    if customer.max_user_id:
        social_accounts.append({
            "provider": "max",
            "max_user_id": customer.max_user_id,
            "first_name": customer.first_name or customer.name or "MAX User",
            "last_name": customer.last_name or customer.surname or "",
            "photo_50": None,
            "screen_name": None,
            "is_subscribed": True,
            "notifications_enabled": customer.is_system_notifications_consented,
            "is_blocked": customer.is_blocked,
            "linked_at": None
        })
        
    return social_accounts


@router.patch("/{customer_id}/social-accounts/vk/{vk_id}")
def update_customer_vk_flags(
    customer_id: int,
    vk_id: int,
    data: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """Обновление флагов блокировки и получения сообщений в ВК для гостя"""
    from app.models.vk_user import VkUser
    
    vk_user = session.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if not vk_user:
        raise HTTPException(status_code=404, detail="VK-профиль не найден")
        
    if "is_blocked" in data:
        vk_user.is_blocked = bool(data["is_blocked"])
    if "notifications_enabled" in data:
        vk_user.notifications_enabled = bool(data["notifications_enabled"])
        
    session.add(vk_user)
    session.commit()
    session.refresh(vk_user)
    return vk_user


@router.patch("/{customer_id}/social-accounts/{provider}/{social_id}")
def update_customer_social_flags(
    customer_id: int,
    provider: str,
    social_id: str,
    data: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """Обновление флагов блокировки и получения уведомлений для соцсетей гостя (VK, Telegram, MAX)"""
    if provider == "vk":
        from app.models.vk_user import VkUser
        try:
            vk_id_int = int(social_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный VK ID")
            
        vk_user = session.exec(select(VkUser).where(VkUser.vk_id == vk_id_int)).first()
        if not vk_user:
            raise HTTPException(status_code=404, detail="VK-профиль не найден")
            
        if "is_blocked" in data:
            vk_user.is_blocked = bool(data["is_blocked"])
        if "notifications_enabled" in data:
            vk_user.notifications_enabled = bool(data["notifications_enabled"])
            
        session.add(vk_user)
        session.commit()
        session.refresh(vk_user)
        return vk_user
        
    elif provider in ("telegram", "max"):
        customer = session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
            
        if "is_blocked" in data:
            customer.is_blocked = bool(data["is_blocked"])
        if "notifications_enabled" in data:
            customer.is_system_notifications_consented = bool(data["notifications_enabled"])
            
        session.add(customer)
        session.commit()
        session.refresh(customer)
        
        return {
            "provider": provider,
            "telegram_id": customer.telegram_id if provider == "telegram" else None,
            "max_user_id": customer.max_user_id if provider == "max" else None,
            "notifications_enabled": customer.is_system_notifications_consented,
            "is_blocked": customer.is_blocked
        }
    else:
        raise HTTPException(status_code=400, detail="Неподдерживаемый провайдер")


@router.get("/maintenance/check-ids")
async def check_customers_ids(session: Session = Depends(get_session)):
    """Поиск клиентов с отсутствующими идентификаторами iiko"""
    from app.services.iiko_sync_service import iiko_sync_service
    customers = await iiko_sync_service.find_customers_missing_iiko_data(session)
    return {
        "count": len(customers),
        "customers": [
            {"id": c.id, "phone": c.phone, "name": c.name, "uid": str(c.uid) if c.uid else None, "iiko_id": str(c.iiko_id) if c.iiko_id else None} 
            for c in customers
        ]
    }


@router.post("/maintenance/merge-by-uid")
async def merge_customers_uid(session: Session = Depends(get_session)):
    """Запуск объединения дубликатов по iiko UID"""
    from app.services.iiko_sync_service import iiko_sync_service
    result = await iiko_sync_service.merge_customers_by_uid(session)
    return result


@router.post("/maintenance/merge-by-phone")
async def merge_customers_phone(session: Session = Depends(get_session)):
    """Запуск объединения дубликатов по номеру телефона"""
    from app.services.iiko_sync_service import iiko_sync_service
    result = await iiko_sync_service.merge_customers_by_phone(session)
    return result

# ================= PREMIUM GUEST CARD ENDPOINTS =================

@router.get("/{customer_id}/olap-stats")
async def get_customer_olap_stats(
    customer_id: int, 
    refresh: bool = Query(default=True, description="Принудительно обновить кэш и БД"),
    session: Session = Depends(get_session)
):
    """Получение расширенной аналитики гостя из iiko Server (OLAP)"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        stats = await iiko_service.get_customer_analytics_olap(customer.phone, session, bypass_cache=refresh)
        
        # [NEW] Сохраняем в базу данных для кэширования
        if stats and not stats.get("error"):
            customer.total_orders_count = stats.get("orders_count", stats.get("total_count", 0))
            customer.total_orders_amount = Decimal(str(stats.get("total_revenue", stats.get("total_sum", 0))))
            customer.total_purchases_sum = customer.total_orders_amount
            customer.total_discount = Decimal(str(stats.get("total_discount", 0)))
            customer.total_items = float(stats.get("total_items", 0))
            customer.average_check = Decimal(str(stats.get("average_check", 0)))
            customer.frequency_days = float(stats.get("frequency_days", 0))
            customer.days_since_last_order = stats.get("days_since_last_order")
            
            if stats.get("first_order_date"):
                try:
                    customer.first_order_date = datetime.fromisoformat(stats["first_order_date"])
                except: pass
            if stats.get("last_order_date"):
                try:
                    customer.last_order_date = datetime.fromisoformat(stats["last_order_date"])
                except: pass
            
            customer.last_olap_sync_at = datetime.now()
            session.add(customer)
            session.commit()
            
        return stats
    except Exception as e:
        logger.error(f"Failed to get OLAP stats for {customer.phone}: {e}")
        # Если ошибка REST_API (лицензия), возвращаем 403
        if "REST_API" in str(e):
            return {"error": "REST_API_LICENSE_REQUIRED", "message": str(e)}
        return {"error": str(e)}

@router.get("/{customer_id}/history")
async def get_customer_history_api(customer_id: int, session: Session = Depends(get_session)):
    """Получение истории заказов гостя напрямую из iiko OLAP"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        history = await iiko_service.get_customer_order_history_olap(customer.phone, session)
        return history
    except Exception as e:
        logger.error(f"Failed to get order history for {customer.phone}: {e}")
        return []

@router.post("/{customer_id}/sync-premium")
async def sync_customer_premium(customer_id: int, session: Session = Depends(get_session)):
    """
    Глубокая синхронизация данных гостя (Profile + Balance + Analytics + Addresses).
    """
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        from app.services.iiko_sync_service import iiko_sync_service
        # Запускаем полную синхронизацию
        await iiko_sync_service.sync_single_customer(session, customer.phone, bypass_cache=True)
        
        # Обновляем объект в текущей сессии
        session.refresh(customer)
        return customer
    except Exception as e:
        logger.error(f"Premium sync failed for {customer.phone}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{customer_id}/adjust-bonuses")
async def adjust_customer_bonuses(
    customer_id: int, 
    data: Dict[str, Any], # Используем Dict для гибкости или BonusAdjustmentRequest если добавим
    session: Session = Depends(get_session)
):
    """Ручное изменение баланса бонусов клиента в iiko"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    amount = data.get("amount")
    comment = data.get("comment", "Ручная корректировка из админ-панели")
    wallet_id = data.get("wallet_id")
    
    if amount is None:
        raise HTTPException(status_code=400, detail="Amount is required")
        
    try:
        # Если wallet_id не передан, пытаемся найти его в сохраненных данных
        if not wallet_id and customer.wallet_balances:
            import json
            try:
                balances = json.loads(customer.wallet_balances)
                if balances and isinstance(balances, list):
                    # Проверяем и 'id' и 'walletId' (iiko Cloud может присылать по-разному)
                    wallet_id = balances[0].get("id") or balances[0].get("walletId")
            except:
                pass
        
        # Если всё еще нет wallet_id, запрашиваем его из iiko
        if not wallet_id:
            info = await iiko_service.get_customer_info(customer.phone)
            balances = info.get("walletBalances", [])
            if balances:
                wallet_id = balances[0].get("id") or balances[0].get("walletId")
        
        if not wallet_id:
            raise HTTPException(status_code=400, detail="Could not find bonus wallet for this customer")
            
        try:
            result = await iiko_service.add_customer_balance(
                customer_id=customer.iiko_customer_id or customer.uid,
                wallet_id=wallet_id,
                amount=float(amount),
                comment=comment
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"Iiko balance update failed: {e}")
            raise HTTPException(status_code=500, detail="Internal error during iiko update")
            
        # После изменения баланса запускаем синхронизацию, чтобы обновить данные в БД
        from app.services.iiko_sync_service import iiko_sync_service
        await iiko_sync_service.sync_single_customer(session, customer.phone)
        
        return {"status": "success", "message": "Balance updated and synced", "result": result}
    except Exception as e:
        logger.error(f"Bonus adjustment failed for {customer.phone}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{customer_id}/bonuses")
async def get_customer_bonuses(customer_id: int, session: Session = Depends(get_session)):
    """Получение истории бонусных операций клиента из БД"""
    from app.models.customer import ClientBonusHistory
    history = session.exec(
        select(ClientBonusHistory)
        .where(ClientBonusHistory.client_id == customer_id)
        .order_by(ClientBonusHistory.transaction_date.desc())
        .limit(100)
    ).all()
    return history
