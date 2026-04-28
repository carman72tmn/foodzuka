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
async def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100000),
    search: Optional[str] = None,
    categories: Optional[List[str]] = Query(None),
    filter_duplicates_phone: bool = Query(False),
    filter_duplicates_uid: bool = Query(False),
    session: Session = Depends(get_session)
):
    """Список клиентов с пагинацией и расширенным поиском"""
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
        
    # Сортировка и пагинация
    query = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    
    # Выполнение запросов
    total = session.exec(count_query).one()
    customers = session.exec(query).all()
    
    return {
        "items": customers,
        "total": total
    }

@router.get("/categories-list")
async def get_categories_list(session: Session = Depends(get_session)):
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

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, session: Session = Depends(get_session)):
    """Детали одного клиента (и запуск фонового обновления)"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    
    # Запускаем фоновую синхронизацию, чтобы при следующем просмотре или обновлении страницы данные были свежими
    try:
        sync_single_customer_task.delay(customer.phone)
    except Exception as e:
        logger.warning(f"Failed to trigger auto-sync for customer {customer.phone}: {e}")
        
    return customer

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
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
    return customer

@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
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
        
    for key, value in update_data.items():
        setattr(customer, key, value)

    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    # Запускаем фоновую синхронизацию
    try:
        sync_single_customer_task.delay(customer.phone)
    except Exception as e:
        logger.warning(f"Failed to trigger sync after update for {customer.phone}: {e}")
        
    return customer

@router.post("/{customer_id}/sync", response_model=CustomerResponse)
async def sync_customer(customer_id: int, session: Session = Depends(get_session)):
    """Синхронизация данных клиента с iiko Loyalty Server"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    try:
        # Получаем данные из iiko
        iiko_data = await iiko_service.get_customer_info(customer.phone)
        
        if iiko_data.get("id"): # Если клиент найден (есть ID)
            # Основные данные
            if iiko_data.get("name"):
                customer.name = iiko_data["name"]
            if iiko_data.get("email"):
                customer.email = iiko_data["email"]
            
            # Дата рождения
            if iiko_data.get("birthday"):
                try:
                    from datetime import date
                    # iiko обычно присылает дату в формате "2024-03-27 00:00:00.000"
                    bday_str = iiko_data["birthday"].split(" ")[0]
                    customer.birthday = datetime.fromisoformat(bday_str)
                except Exception:
                    pass
            
            # Расширенные данные
            customer.iiko_customer_id = iiko_data.get("id")
            customer.city = iiko_data.get("city")
            customer.notes = iiko_data.get("comment")
            
            # Риски
            if "shouldBeCheckedForRisk" in iiko_data:
                customer.is_risk = iiko_data.get("shouldBeCheckedForRisk", False)
            
            # Категории (сохраняем только имена для фронтенда)
            if "categories" in iiko_data:
                category_names = []
                for cat in iiko_data["categories"]:
                    if isinstance(cat, dict) and cat.get("name"):
                        category_names.append(cat["name"])
                customer.loyalty_categories = json.dumps(category_names, ensure_ascii=False)
                customer.categories = customer.loyalty_categories
            
            # Адреса
            if "deliveryAddresses" in iiko_data:
                customer.addresses = json.dumps(iiko_data["deliveryAddresses"], ensure_ascii=False)

            # Бонусы и кошельки
            if "walletBalances" in iiko_data:
                total_bonuses = sum(float(b.get("balance", 0)) for b in iiko_data["walletBalances"])
                customer.bonus_points = Decimal(str(total_bonuses))
                customer.wallet_balances = json.dumps(iiko_data["walletBalances"], ensure_ascii=False)
            
            customer.updated_at = datetime.now(timezone.utc)
            
            session.add(customer)
            session.commit()
            session.refresh(customer)
            
        return customer
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/{customer_id}/full-sync")
async def full_sync_customer(customer_id: int, session: Session = Depends(get_session)):
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
async def get_local_bonus_history(
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
async def get_local_addresses(
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
async def get_local_phones(
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

@router.post("/import")
async def import_customers(
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
async def sync_all_customers(
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
async def get_sync_status(sync_id: int, session: Session = Depends(get_session)):
    """Получение прогресса синхронизации"""
    status = session.get(SyncStatus, sync_id)
    if not status:
        raise HTTPException(status_code=404, detail="Sync status not found")
    return status

@router.get("/sync-latest")
async def get_latest_sync_status(session: Session = Depends(get_session)):
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
            
        # Удаляем None и пустые значения
        iiko_payload = {k: v for k, v in iiko_payload.items() if v is not None and str(v).strip() != ""}
        
        logger.info(f"Updating customer {customer_id} in iiko with payload: {iiko_payload}")
        
        result = await iiko_service.create_or_update_customer(iiko_payload)
        
        # В ответе iiko может быть id или вложенный объект customer
        res_id = result.get("id") or result.get("customer", {}).get("id")
        
        if res_id:
            # Обновляем локально
            for key, value in customer_data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            
            customer.updated_at = datetime.now(timezone.utc)
            session.add(customer)
            session.commit()
            session.refresh(customer)
            
            # Запускаем фоновую синхронизацию для обновления всех полей из iiko
            try:
                sync_single_customer_task.delay(customer.phone)
            except Exception as e:
                logger.warning(f"Failed to trigger sync after iiko update for {customer.phone}: {e}")
            
        return result
    except Exception as e:
        logger.error(f"iiko update failed for customer {customer_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"iiko update failed: {str(e)}")

@router.get("/{customer_id}/vk-account")
async def get_customer_vk_account(customer_id: int, session: Session = Depends(get_session)):
    """Получение связанного VK аккаунта клиента"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.vk_user_id:
        return None
        
    vk_account = session.exec(select(VkBotAccount).where(VkBotAccount.vk_user_id == customer.vk_user_id)).first()
    return vk_account

@router.post("/{customer_id}/vk-link")
async def link_customer_vk(
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


@router.get("/maintenance/check-ids")
async def check_customers_ids(session: Session = Depends(get_session)):
    """Поиск клиентов с отсутствующими идентификаторами iiko"""
    from app.services.iiko_sync_service import iiko_sync_service
    customers = await iiko_sync_service.find_customers_missing_iiko_data(session)
    return {
        "count": len(customers),
        "customers": [
            {"id": c.id, "phone": c.phone, "name": c.name, "uid": c.uid, "iiko_id": c.iiko_id} 
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
async def get_customer_olap_stats(customer_id: int, session: Session = Depends(get_session)):
    """Получение расширенной аналитики гостя из iiko Server (OLAP)"""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        stats = await iiko_service.get_customer_analytics_olap(customer.phone, session)
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
        await iiko_sync_service.sync_single_customer(session, customer.phone)
        
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
                    # Ищем кошелек, который не нулевой или первый попавшийся
                    wallet_id = balances[0].get("walletId")
            except:
                pass
        
        # Если всё еще нет wallet_id, запрашиваем его из iiko
        if not wallet_id:
            info = await iiko_service.get_customer_info(customer.phone)
            balances = info.get("walletBalances", [])
            if balances:
                wallet_id = balances[0].get("walletId")
        
        if not wallet_id:
            raise HTTPException(status_code=400, detail="Could not find bonus wallet for this customer")
            
        result = await iiko_service.add_customer_balance(
            customer_id=customer.iiko_customer_id or customer.uid,
            wallet_id=wallet_id,
            amount=float(amount),
            comment=comment
        )
        
        # После изменения баланса запускаем синхронизацию, чтобы обновить данные в БД
        from app.services.iiko_sync_service import iiko_sync_service
        await iiko_sync_service.sync_single_customer(session, customer.phone)
        
        return {"status": "success", "result": result}
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
