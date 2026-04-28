from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func, or_
from typing import List, Optional
from app.api.deps import get_db, get_current_active_superuser
from app.models.vk_bot import (
    VkBotAccount, VkBotGroup, VkBotSubscription, VkBotMessageLog, 
    VkBotAccountGroupLink, MessageStatus, VkTemplate, VkMailing
)
from app.services.vk_bot_service import vk_bot_service
from app.services.vk_notification_router import vk_notification_router
from pydantic import BaseModel

class CustomerSearchResponse(BaseModel):
    id: int
    name: Optional[str]
    phone: str

router = APIRouter(dependencies=[Depends(get_current_active_superuser)])

# --- Схемы данных ---

class AccountCreate(BaseModel):
    vk_link: str
    name: str
    phone: Optional[str] = None
    employee_id: Optional[int] = None

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[int] = None
    is_active: Optional[bool] = None
    enabled_events: Optional[List[str]] = None

class VkTemplateCreate(BaseModel):
    name: str
    text: str
    keyboard_json: Optional[str] = None

class ManualBroadcast(BaseModel):
    text: str
    account_ids: Optional[List[int]] = None
    group_ids: Optional[List[int]] = None
    template_id: Optional[int] = None

class SubscriptionUpdate(BaseModel):
    account_id: int
    event_type: str
    delivery_mode: str
    interval_minutes: int = 0
    active_start_hour: int = 0
    active_end_hour: int = 23

# --- Аккаунты ---

@router.get("/accounts", response_model=List[VkBotAccount])
def get_accounts(
    search: Optional[str] = Query(None, description="Поиск по имени, ID или телефону"),
    db: Session = Depends(get_db)
):
    statement = select(VkBotAccount)
    if search:
        # Проверяем, является ли поиск числом (ID VK)
        is_digit = search.isdigit()
        if is_digit:
            statement = statement.where(
                or_(
                    VkBotAccount.vk_user_id == int(search),
                    VkBotAccount.phone.contains(search),
                    VkBotAccount.name.contains(search)
                )
            )
        else:
            statement = statement.where(
                or_(
                    VkBotAccount.name.contains(search),
                    VkBotAccount.phone.contains(search)
                )
            )
    return db.exec(statement).all()

@router.get("/employees/search")
def search_employees(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """Поиск сотрудников для привязки к VK"""
    from app.models.employee import Employee
    statement = select(Employee).where(
        or_(
            Employee.name.contains(q),
            Employee.phone.contains(q)
        )
    ).limit(10)
    return db.exec(statement).all()

@router.get("/customers/search", response_model=List[CustomerSearchResponse])
def search_customers(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """Поиск по базе клиентов для автозаполнения"""
    from app.models.customer import Customer
    statement = select(Customer).where(
        or_(
            Customer.phone.contains(q),
            Customer.name.contains(q)
        )
    ).limit(10)
    return db.exec(statement).all()

@router.post("/accounts")
async def add_account(data: AccountCreate, db: Session = Depends(get_db)):
    # Резолвим screen_name
    vk_id = await vk_bot_service.resolve_screen_name(data.vk_link)
    if not vk_id:
        raise HTTPException(status_code=400, detail="Не удалось найти пользователя VK по ссылке")

    # Проверяем, нет ли уже такого
    existing = db.exec(select(VkBotAccount).where(VkBotAccount.vk_user_id == vk_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Этот аккаунт уже добавлен")

    new_account = VkBotAccount(
        vk_user_id=vk_id, 
        name=data.name, 
        phone=data.phone,
        employee_id=data.employee_id
    )
    db.add(new_account)
    
    # Сразу связываем с клиентом, если найден телефон
    if data.phone:
        from app.models.customer import Customer
        customer = db.exec(select(Customer).where(Customer.phone == data.phone)).first()
        if customer:
            customer.vk_user_id = vk_id
            db.add(customer)
            
            # Запускаем синхронизацию данных клиента из iiko
            from app.tasks.customer_tasks import sync_single_customer_task
            sync_single_customer_task.delay(customer.phone)

    db.commit()
    db.refresh(new_account)
    return new_account

@router.patch("/accounts/{account_id}")
def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(account, key, value)
    
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    db.delete(account)
    db.commit()
    return {"status": "success"}

@router.post("/accounts/{account_id}/verify")
async def verify_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    result = await vk_bot_service.send_message(
        user_id=account.vk_user_id,
        message="🔧 Проверка связи! Вы успешно подписаны на уведомления FoodZuka.",
        account_id=account.id,
        event_type="verification"
    )

    if result["success"]:
        account.is_verified = True
        db.add(account)
        db.commit()
        return {"status": "success", "message": "Проверочное сообщение отправлено"}
    else:
        return {"status": "error", "message": result["error"]}

# --- Подписки ---

@router.get("/subscriptions", response_model=List[VkBotSubscription])
def get_subscriptions(db: Session = Depends(get_db)):
    return db.exec(select(VkBotSubscription)).all()

@router.post("/subscriptions")
def update_subscription(data: SubscriptionUpdate, db: Session = Depends(get_db)):
    statement = select(VkBotSubscription).where(
        VkBotSubscription.account_id == data.account_id,
        VkBotSubscription.event_type == data.event_type
    )
    sub = db.exec(statement).first()

    if not sub:
        sub = VkBotSubscription(
            account_id=data.account_id,
            event_type=data.event_type
        )
    
    sub.delivery_mode = data.delivery_mode
    sub.interval_minutes = data.interval_minutes
    sub.active_start_hour = data.active_start_hour
    sub.active_end_hour = data.active_end_hour
    
    db.add(sub)
    db.commit()
    return {"status": "success"}

@router.get("/accounts/{account_id}/subscriptions", response_model=List[VkBotSubscription])
def get_account_subscriptions(account_id: int, db: Session = Depends(get_db)):
    return db.exec(select(VkBotSubscription).where(VkBotSubscription.account_id == account_id)).all()

@router.delete("/subscriptions/{subscription_id}")
def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    sub = db.get(VkBotSubscription, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    db.delete(sub)
    db.commit()
    return {"status": "success"}

# --- Шаблоны ---

@router.get("/templates", response_model=List[VkTemplate])
def get_templates(db: Session = Depends(get_db)):
    return db.exec(select(VkTemplate)).all()

@router.get("/templates/{template_id}", response_model=VkTemplate)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return template

@router.post("/templates")
def create_template(data: VkTemplateCreate, db: Session = Depends(get_db)):
    template = VkTemplate(**data.dict())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.patch("/templates/{template_id}")
def update_template(template_id: int, data: VkTemplateCreate, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(template, key, value)
    
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    db.delete(template)
    db.commit()
    return {"status": "success"}

@router.get("/variables")
def get_template_variables():
    """Возвращает список доступных переменных и типов событий"""
    return {
        "variables": {
            "Заказ": {
                "order.external_number": "Номер заказа (из iiko)",
                "order.total_amount": "Сумма без скидки",
                "order.total_with_discount": "Итоговая сумма (к оплате)",
                "order.final_price": "Итоговая сумма (к оплате) - синоним",
                "order.total_discount": "Сумма скидки",
                "order.discount_sum": "Сумма скидки - синоним",
                "order.items_summary": "Состав заказа с ценами (полный)",
                "order.customer_name": "Имя гостя",
                "order.customer_phone": "Телефон гостя",
                "order.address": "Адрес доставки",
                "order.delivery_time": "Время доставки (ожидаемое)",
                "order.comment": "Комментарий к заказу",
                "order.courier_name": "Имя курьера",
                "order.map_yandex": "Ссылка на Яндекс.Карты",
                "order.map_2gis": "Ссылка на 2ГИС",
            },
            "Клиент": {
                "customer.name": "Имя в базе",
                "customer.phone": "Телефон",
                "customer.bonus_points": "Баланс бонусов",
                "customer.categories": "Категории (метки) клиента",
                "customer.notes": "Заметки о клиенте"
            }
        },
        "events": [
            {"type": "order_new", "name": "Новый заказ"},
            {"type": "order_status_update", "name": "Изменение статуса заказа"},
            {"type": "order_amount_changed", "name": "Изменение суммы заказа"},
            {"type": "order_items_changed", "name": "Изменение состава блюд"},
            {"type": "order_time_changed", "name": "Изменение времени доставки"},
            {"type": "order_address_changed", "name": "Изменение адреса доставки"},
            {"type": "courier_assigned", "name": "Назначение курьера"},
            {"type": "order_cancelled", "name": "Отмена заказа"},
        ]
    }

# --- Рассылки ---

@router.post("/broadcast")
async def send_broadcast(data: ManualBroadcast, db: Session = Depends(get_db)):
    message_text = data.text
    keyboard = None
    
    if data.template_id:
        template = db.get(VkTemplate, data.template_id)
        if template:
            message_text = template.text
            keyboard = template.keyboard_json

    await vk_notification_router.send_manual_broadcast(
        text=message_text,
        account_ids=data.account_ids,
        group_ids=data.group_ids,
        keyboard=keyboard
    )
    return {"status": "success", "message": "Рассылка запущена"}

# --- Логи ---

@router.get("/logs")
def get_logs(limit: int = 1000, db: Session = Depends(get_db)):
    statement = select(VkBotMessageLog).order_by(VkBotMessageLog.created_at.desc()).limit(limit)
    return db.exec(statement).all()

# --- Группы ---

@router.get("/groups", response_model=List[VkBotGroup])
def get_groups(db: Session = Depends(get_db)):
    return db.exec(select(VkBotGroup)).all()
