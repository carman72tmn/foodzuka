from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func, or_, delete
from typing import List, Optional, Any, Dict
from app.api.deps import get_db, get_current_active_superuser, require_permission
from app.models.user import User
from app.models.vk_bot import (
    VkBotAccount, VkBotGroup, VkBotSubscription, VkBotMessageLog, 
    VkBotAccountGroupLink, MessageStatus, VkTemplate, VkMailing, DeliveryMode
)
from app.services.vk_bot_service import vk_bot_service
from app.services.vk_notification_router import vk_notification_router
from pydantic import BaseModel

class CustomerSearchResponse(BaseModel):
    id: int
    name: Optional[str]
    phone: str

router = APIRouter()

# --- Схемы данных ---

class AccountCreate(BaseModel):
    vk_link: Optional[str] = None
    name: str
    phone: Optional[str] = None
    employee_id: Optional[int] = None
    user_id: Optional[int] = None
    tg_user_id: Optional[int] = None
    max_user_id: Optional[str] = None
    use_vk: bool = True
    use_tg: bool = False
    use_max: bool = False
    use_sms: bool = False
    send_payment_qr: bool = False
    payment_qr_mode: str = "all"
    is_courier: bool = False
    max_bot_id: Optional[int] = None
    max_send_mode: Optional[str] = "cascade"
    edit_existing_message: Optional[bool] = True
    collapse_on_delivered: Optional[bool] = True
    show_courier_action_buttons: Optional[bool] = True

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[int] = None
    user_id: Optional[int] = None
    is_active: Optional[bool] = None
    enabled_events: Optional[List[str]] = None
    vk_user_id: Optional[int] = None
    tg_user_id: Optional[int] = None
    max_user_id: Optional[str] = None
    use_vk: Optional[bool] = None
    use_tg: Optional[bool] = None
    use_max: Optional[bool] = None
    use_sms: Optional[bool] = None
    send_payment_qr: Optional[bool] = None
    payment_qr_mode: Optional[str] = None
    is_courier: Optional[bool] = None
    max_bot_id: Optional[int] = None
    max_send_mode: Optional[str] = None

class ChannelToggleRequest(BaseModel):
    channel: str # vk, tg, max, sms
    enabled: bool

class TemplateBotSetRequest(BaseModel):
    vk_bot_id: Optional[int] = None

class TemplateMaxBotSetRequest(BaseModel):
    max_bot_id: Optional[int] = None
    max_send_mode: Optional[str] = "cascade"
    edit_existing_message: Optional[bool] = True
    collapse_on_delivered: Optional[bool] = True
    show_courier_action_buttons: Optional[bool] = True

class BulkChainsToggleRequest(BaseModel):
    enabled: bool

class VkTemplateCreate(BaseModel):
    name: str
    text: str
    keyboard_json: Optional[str] = None
    event_type: Optional[str] = None
    keyboard_telegram: Optional[str] = None
    keyboard_max: Optional[str] = None
    target_mode: Optional[str] = "all"
    target_roles: Optional[Any] = None
    target_accounts: Optional[Any] = None
    is_active: Optional[bool] = True
    include_statuses: Optional[str] = None
    attach_sbp_qr: Optional[bool] = False
    chain_config: Optional[str] = None
    description: Optional[str] = None
    vk_bot_id: Optional[int] = None
    send_vk: Optional[bool] = True
    send_tg: Optional[bool] = False
    send_max: Optional[bool] = False
    send_sms: Optional[bool] = False
    max_bot_id: Optional[int] = None
    max_send_mode: Optional[str] = "cascade"
    edit_existing_message: Optional[bool] = True
    collapse_on_delivered: Optional[bool] = True
    show_courier_action_buttons: Optional[bool] = True

class VkTemplateUpdate(BaseModel):
    name: Optional[str] = None
    text: Optional[str] = None
    keyboard_json: Optional[str] = None
    event_type: Optional[str] = None
    keyboard_telegram: Optional[str] = None
    keyboard_max: Optional[str] = None
    target_mode: Optional[str] = None
    target_roles: Optional[Any] = None
    target_accounts: Optional[Any] = None
    is_active: Optional[bool] = None
    include_statuses: Optional[str] = None
    attach_sbp_qr: Optional[bool] = None
    chain_config: Optional[str] = None
    description: Optional[str] = None
    vk_bot_id: Optional[int] = None
    send_vk: Optional[bool] = None
    send_tg: Optional[bool] = None
    send_max: Optional[bool] = None
    send_sms: Optional[bool] = None
    max_bot_id: Optional[int] = None
    max_send_mode: Optional[str] = None
    edit_existing_message: Optional[bool] = None
    collapse_on_delivered: Optional[bool] = None
    show_courier_action_buttons: Optional[bool] = None

class SbpQrPreviewRequest(BaseModel):
    order_number: Optional[str] = "104"
    amount: float = 1850.0
    delivery_address: Optional[str] = "г. Тюмень, ул. Республики, д. 142, кв. 15"

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
    send_vk: bool = True
    send_tg: bool = False
    send_max: bool = False
    send_sms: bool = False

class CourierChainsToggleRequest(BaseModel):
    allow_courier_chains: Optional[bool] = None
    channel: Optional[str] = None
    enabled: Optional[bool] = None
    send_vk: Optional[bool] = None
    send_tg: Optional[bool] = None
    send_max: Optional[bool] = None
    send_sms: Optional[bool] = None

class TemplateSubscriptionToggleRequest(BaseModel):
    template_id: Optional[int] = None
    event_type: Optional[str] = None
    subscribed: Optional[bool] = True
    channel: Optional[str] = None
    enabled: Optional[bool] = None
    send_vk: Optional[bool] = None
    send_tg: Optional[bool] = None
    send_max: Optional[bool] = None
    send_sms: Optional[bool] = None
    delivery_mode: Optional[str] = "realtime"
    interval_minutes: Optional[int] = 0
    active_start_hour: Optional[int] = 0
    active_end_hour: Optional[int] = 23

class BulkTemplatesToggleRequest(BaseModel):
    action: str # "enable_all", "disable_all", "set_channel"
    channel: Optional[str] = None # "vk", "tg", "max", "sms"
    value: Optional[bool] = None

# --- Аккаунты ---

@router.get("/accounts", response_model=List[VkBotAccount], dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_accounts(
    search: Optional[str] = Query(None, description="Поиск по имени, ID или телефону"),
    db: Session = Depends(get_db)
):
    statement = select(VkBotAccount)
    if search:
        is_digit = search.isdigit()
        if is_digit:
            statement = statement.where(
                or_(
                    VkBotAccount.vk_user_id == int(search),
                    VkBotAccount.tg_user_id == int(search),
                    VkBotAccount.phone.contains(search),
                    VkBotAccount.name.contains(search)
                )
            )
        else:
            statement = statement.where(
                or_(
                    VkBotAccount.name.contains(search),
                    VkBotAccount.phone.contains(search),
                    VkBotAccount.max_user_id.contains(search)
                )
            )
    return db.exec(statement).all()

@router.get("/employees/search", dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def search_employees(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Поиск сотрудников для привязки к VK/уведомлениям"""
    from app.models.employee import Employee
    statement = select(Employee).where(Employee.status == "Active")
    if q:
        clean_q = q.strip()
        if clean_q:
            statement = statement.where(
                or_(
                    Employee.name.ilike(f"%{clean_q}%"),
                    Employee.phone.ilike(f"%{clean_q}%"),
                    Employee.role.ilike(f"%{clean_q}%")
                )
            )
    statement = statement.order_by(Employee.name).limit(50)
    return db.exec(statement).all()

@router.get("/users/search", dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def search_users(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Поиск пользователей админ-панели для назначения получателями"""
    from app.models.user import User
    statement = select(User).where(User.is_active == True)
    if q:
        clean_q = q.strip()
        if clean_q:
            statement = statement.where(
                or_(
                    User.username.ilike(f"%{clean_q}%"),
                    User.full_name.ilike(f"%{clean_q}%"),
                    User.email.ilike(f"%{clean_q}%")
                )
            )
    statement = statement.order_by(User.username).limit(50)
    users = db.exec(statement).all()
    result = []
    for u in users:
        emp_name = u.employee.name if u.employee else None
        emp_phone = u.employee.phone if u.employee else None
        result.append({
            "id": u.id,
            "username": u.username,
            "name": u.full_name or u.username,
            "email": u.email,
            "vk_user_id": u.vk_user_id,
            "employee_id": u.employee.id if u.employee else None,
            "employee_name": emp_name,
            "phone": emp_phone,
            "role_name": u.role.name if u.role else None
        })
    return result

@router.get("/customers/search", response_model=List[CustomerSearchResponse], dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def search_customers(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Поиск по базе клиентов для автозаполнения"""
    from app.models.customer import Customer
    if not q or len(q.strip()) < 2:
        return []
    clean_q = q.strip()
    statement = select(Customer).where(
        or_(
            Customer.phone.ilike(f"%{clean_q}%"),
            Customer.name.ilike(f"%{clean_q}%"),
            Customer.surname.ilike(f"%{clean_q}%")
        )
    ).limit(15)
    return db.exec(statement).all()


async def validate_courier_link(employee_id: Optional[int], db: Session) -> bool:
    """Проверка, является ли сотрудник курьером в iiko и в локальной БД"""
    if not employee_id or employee_id <= 0:
        return False
    from app.models.employee import Employee
    from app.models.iiko_settings import IikoSettings
    from app.services.iiko_service import iiko_service

    emp = db.get(Employee, employee_id)
    if not emp:
        return False

    # 1. Проверка по локальным признакам роли
    role_lower = str(emp.role or "").lower()
    name_lower = str(emp.name or "").lower()
    if emp.is_courier or "курьер" in role_lower or "driver" in role_lower or "курьер" in name_lower:
        return True

    # 2. Проверка через iiko Cloud API
    if emp.iiko_id:
        settings = db.exec(select(IikoSettings)).first()
        if settings and settings.organization_id:
            try:
                couriers = await iiko_service.get_couriers(settings.organization_id)
                for c in couriers:
                    if c.get("id") == emp.iiko_id:
                        emp.is_courier = True
                        db.add(emp)
                        db.commit()
                        return True
            except Exception as e:
                logger.warning(f"Failed to check courier in iiko: {e}")
    return False


@router.get("/accounts/check-courier/{employee_id}")
async def check_courier_link(employee_id: int, db: Session = Depends(get_db)):
    """Проверка привязки сотрудника к курьеру в iiko для фронтенда"""
    from app.models.employee import Employee
    emp = db.get(Employee, employee_id)
    if not emp:
        return {"status": "error", "is_courier": False, "message": "Сотрудник не найден"}
    
    is_courier = await validate_courier_link(employee_id, db)
    return {
        "status": "success",
        "is_courier": is_courier,
        "employee_name": emp.name,
        "iiko_id": emp.iiko_id,
        "role": emp.role
    }


DEFAULT_SYSTEM_EVENTS = [
    "order_new", "order_status_update", "order_amount_changed",
    "order_items_changed", "order_time_changed", "order_address_changed",
    "order_cancelled", "change_cooking_time", "courier_assigned",
    "shift_open", "shift_close"
]


@router.post("/accounts", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
async def add_account(data: AccountCreate, db: Session = Depends(get_db)):
    vk_id = None
    if data.vk_link:
        # Резолвим screen_name
        vk_id = await vk_bot_service.resolve_screen_name(data.vk_link)
        if not vk_id:
            raise HTTPException(status_code=400, detail="Не удалось найти пользователя VK по ссылке")

    emp_id = data.employee_id if (data.employee_id and data.employee_id > 0) else None
    usr_id = data.user_id if (data.user_id and data.user_id > 0) else None

    # Валидация курьера
    is_courier_flag = bool(data.is_courier)
    if is_courier_flag:
        is_valid_courier = await validate_courier_link(emp_id, db)
        if not is_valid_courier:
            raise HTTPException(
                status_code=400, 
                detail="Сотрудник не является курьером в iiko! Выберите сотрудника с ролью курьера в iiko."
            )
    elif emp_id:
        # Автоматическая проверка: если сотрудник курьер в iiko, ставим флаг
        if await validate_courier_link(emp_id, db):
            is_courier_flag = True

    max_uid = (data.max_user_id or "").strip()
    if not max_uid and data.phone:
        max_uid = data.phone.strip()

    new_account = VkBotAccount(
        vk_user_id=vk_id, 
        name=data.name, 
        phone=data.phone,
        employee_id=emp_id,
        user_id=usr_id,
        tg_user_id=data.tg_user_id,
        max_user_id=max_uid or None,
        use_vk=data.use_vk,
        use_tg=data.use_tg,
        use_max=data.use_max,
        use_sms=data.use_sms,
        send_payment_qr=data.send_payment_qr,
        payment_qr_mode=data.payment_qr_mode,
        is_courier=is_courier_flag,
        max_bot_id=data.max_bot_id,
        max_send_mode=data.max_send_mode or "cascade"
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    # Автоматически создаем базовые подписки на системные события с выбранными каналами
    for ev in DEFAULT_SYSTEM_EVENTS:
        sub = VkBotSubscription(
            account_id=new_account.id,
            event_type=ev,
            delivery_mode=DeliveryMode.REALTIME,
            interval_minutes=0,
            active_start_hour=0,
            active_end_hour=23,
            send_vk=bool(new_account.use_vk),
            send_tg=bool(new_account.use_tg),
            send_max=bool(new_account.use_max),
            send_sms=bool(new_account.use_sms)
        )
        db.add(sub)
    
    # Сразу связываем с клиентом, если найден телефон
    if data.phone:
        from app.models.customer import Customer
        customer = db.exec(select(Customer).where(Customer.phone == data.phone)).first()
        if customer:
            if vk_id:
                customer.vk_user_id = vk_id
            db.add(customer)
            
            # Запускаем синхронизацию данных клиента из iiko
            from app.tasks.customer_tasks import sync_single_customer_task
            sync_single_customer_task.delay(customer.phone)

    db.commit()
    db.refresh(new_account)
    return new_account

@router.patch("/accounts/{account_id}", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
async def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    update_data = data.dict(exclude_unset=True)
    if "employee_id" in update_data:
        val = update_data["employee_id"]
        if val is not None and val <= 0:
            update_data["employee_id"] = None

    if "user_id" in update_data:
        u_val = update_data["user_id"]
        if u_val is not None and u_val <= 0:
            update_data["user_id"] = None

    if "max_user_id" in update_data:
        val = (update_data["max_user_id"] or "").strip()
        if not val and (update_data.get("phone") or account.phone):
            val = (update_data.get("phone") or account.phone or "").strip()
        update_data["max_user_id"] = val or None

    target_emp_id = update_data.get("employee_id", account.employee_id)

    # Валидация флага курьера при изменении
    if "is_courier" in update_data and update_data["is_courier"]:
        is_valid_courier = await validate_courier_link(target_emp_id, db)
        if not is_valid_courier:
            raise HTTPException(
                status_code=400, 
                detail="Сотрудник не является курьером в iiko! Выберите сотрудника с ролью курьера в iiko."
            )
    elif "employee_id" in update_data and target_emp_id and "is_courier" not in update_data:
        # Автоматическая связка при смене сотрудника
        if await validate_courier_link(target_emp_id, db):
            update_data["is_courier"] = True

    channel_changed = any(k in update_data for k in ("use_vk", "use_tg", "use_max", "use_sms"))

    for key, value in update_data.items():
        setattr(account, key, value)
    
    db.add(account)

    # Автоматическая синхронизация каналов в подписках при изменении каналов по умолчанию
    if channel_changed:
        subs = db.exec(select(VkBotSubscription).where(VkBotSubscription.account_id == account.id)).all()
        if not subs:
            for ev in DEFAULT_SYSTEM_EVENTS:
                sub = VkBotSubscription(
                    account_id=account.id,
                    event_type=ev,
                    delivery_mode=DeliveryMode.REALTIME,
                    interval_minutes=0,
                    active_start_hour=0,
                    active_end_hour=23,
                    send_vk=bool(account.use_vk),
                    send_tg=bool(account.use_tg),
                    send_max=bool(account.use_max),
                    send_sms=bool(account.use_sms)
                )
                db.add(sub)
        else:
            for s in subs:
                if "use_vk" in update_data:
                    s.send_vk = bool(account.use_vk)
                if "use_tg" in update_data:
                    s.send_tg = bool(account.use_tg)
                if "use_max" in update_data:
                    s.send_max = bool(account.use_max)
                if "use_sms" in update_data:
                    s.send_sms = bool(account.use_sms)
                db.add(s)

    db.commit()
    db.refresh(account)
    return account


@router.post("/accounts/{account_id}/toggle-channel", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def toggle_account_channel(account_id: int, data: ChannelToggleRequest, db: Session = Depends(get_db)):
    """Быстрое переключение канала доставки (VK, TG, MAX, SMS) для сотрудника"""
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    ch = data.channel.lower().strip()
    if ch == "vk":
        account.use_vk = data.enabled
    elif ch == "tg":
        account.use_tg = data.enabled
    elif ch == "max":
        account.use_max = data.enabled
    elif ch == "sms":
        account.use_sms = data.enabled
    else:
        raise HTTPException(status_code=400, detail=f"Неизвестный канал: {data.channel}")
    
    db.add(account)
    
    # Синхронизируем подписки аккаунта
    subs = db.exec(select(VkBotSubscription).where(VkBotSubscription.account_id == account.id)).all()
    if not subs:
        for ev in DEFAULT_SYSTEM_EVENTS:
            sub = VkBotSubscription(
                account_id=account.id,
                event_type=ev,
                send_vk=bool(account.use_vk),
                send_tg=bool(account.use_tg),
                send_max=bool(account.use_max),
                send_sms=bool(account.use_sms)
            )
            db.add(sub)
    else:
        for s in subs:
            if ch == "vk": s.send_vk = data.enabled
            elif ch == "tg": s.send_tg = data.enabled
            elif ch == "max": s.send_max = data.enabled
            elif ch == "sms": s.send_sms = data.enabled
            db.add(s)
            
    db.commit()
    db.refresh(account)
    return account


@router.post("/accounts/{account_id}/bulk-toggle-subscriptions", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def bulk_toggle_subscriptions(account_id: int, data: ChannelToggleRequest, db: Session = Depends(get_db)):
    """Массовое включение/выключение канала во всех событиях получателя"""
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    ch = data.channel.lower().strip()
    if data.enabled:
        if ch == "vk": account.use_vk = True
        elif ch == "tg": account.use_tg = True
        elif ch == "max": account.use_max = True
        elif ch == "sms": account.use_sms = True
        db.add(account)
        
    subs = db.exec(select(VkBotSubscription).where(VkBotSubscription.account_id == account.id)).all()
    if not subs:
        for ev in DEFAULT_SYSTEM_EVENTS:
            sub = VkBotSubscription(
                account_id=account.id,
                event_type=ev,
                send_vk=(data.enabled if ch == "vk" else account.use_vk),
                send_tg=(data.enabled if ch == "tg" else account.use_tg),
                send_max=(data.enabled if ch == "max" else account.use_max),
                send_sms=(data.enabled if ch == "sms" else account.use_sms)
            )
            db.add(sub)
    else:
        for s in subs:
            if ch == "vk": s.send_vk = data.enabled
            elif ch == "tg": s.send_tg = data.enabled
            elif ch == "max": s.send_max = data.enabled
            elif ch == "sms": s.send_sms = data.enabled
            db.add(s)
            
    db.commit()
    return {"status": "success", "channel": ch, "enabled": data.enabled}

@router.delete("/accounts/{account_id}", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    # Удаляем связи с группами в таблице vk_bot_account_group_links
    db.execute(delete(VkBotAccountGroupLink).where(VkBotAccountGroupLink.account_id == account_id))
    
    # Удаляем подписки получателя
    db.execute(delete(VkBotSubscription).where(VkBotSubscription.account_id == account_id))
    
    # Удаляем логи сообщений получателя
    db.execute(delete(VkBotMessageLog).where(VkBotMessageLog.account_id == account_id))
    
    # Удаляем сам аккаунт получателя
    db.delete(account)
    db.commit()
    return {"status": "success"}

@router.post("/accounts/{account_id}/verify", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
async def verify_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    if not account.vk_user_id:
        raise HTTPException(status_code=400, detail="VK ID не привязан")

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

@router.post("/accounts/{account_id}/verify/tg", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
async def verify_account_tg(account_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    if not account.tg_user_id:
        raise HTTPException(status_code=400, detail="Telegram ID не привязан")

    from app.models.bot_settings import BotSettings
    import os
    import httpx
    
    bot_settings = db.exec(select(BotSettings)).first()
    token = bot_settings.telegram_bot_token if (bot_settings and bot_settings.telegram_bot_token) else os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        raise HTTPException(status_code=500, detail="Не настроен токен Telegram-бота в системе")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": account.tg_user_id,
        "text": "🔧 <b>Проверка связи!</b> Вы успешно привязали Telegram к Системным рассылкам FoodZuka.",
        "parse_mode": "HTML"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            if response.status_code == 200 and result.get("ok"):
                account.is_tg_verified = True
                db.add(account)
                db.commit()
                return {"status": "success", "message": "Проверочное сообщение в Telegram успешно отправлено"}
            else:
                description = result.get("description", "Unknown error")
                return {"status": "error", "message": f"Ошибка Telegram API: {description}"}
    except Exception as e:
        return {"status": "error", "message": f"Не удалось связаться с Telegram: {str(e)}"}

@router.post("/accounts/{account_id}/verify/max", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
async def verify_account_max(account_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    target = account.max_user_id or account.phone
    if not target:
        raise HTTPException(status_code=400, detail="Ни телефон для привязки MAX, ни основной телефон не привязаны")

    from app.models.max_settings import MaxSettings
    from app.services.max_service import send_max_message

    settings = db.exec(select(MaxSettings)).first()
    if not settings or not settings.is_active:
        raise HTTPException(status_code=400, detail="Интеграция с MAX Messenger не активна в настройках")

    digits = "".join(filter(str.isdigit, str(target)))
    phone_clean = None
    if len(digits) == 11 and digits.startswith("8"):
        phone_clean = "7" + digits[1:]
    elif len(digits) == 10:
        phone_clean = "7" + digits
    elif len(digits) == 11 and digits.startswith("7"):
        phone_clean = digits

    res = await send_max_message(
        recipient=phone_clean if phone_clean else target,
        phone=phone_clean,
        text="🔧 Проверка связи! Вы успешно привязали MAX Messenger к Системным рассылкам FoodZuka.",
        session=db,
        settings=settings,
        bot_id=account.max_bot_id,
        prefer_channel=account.max_send_mode or "cascade"
    )

    if res.get("success"):
        account.is_max_verified = True
        if not account.max_user_id and phone_clean:
            account.max_user_id = f"+{phone_clean}"
        db.add(account)
        db.commit()
        via = res.get("via") or res.get("channel_type")
        via_desc = "через официального бота" if via == "bot" else "от личного аккаунта MAX (Web Bridge)"
        return {
            "status": "success", 
            "message": f"Проверочное сообщение в MAX успешно отправлено ({via_desc})",
            "via": via
        }
    else:
        err = res.get("error") or "Не удалось отправить сообщение через MAX. Проверьте подключение ботов или личного аккаунта."
        return {"status": "error", "message": err}

# --- Подписки ---

@router.get("/subscriptions", response_model=List[VkBotSubscription], dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_subscriptions(db: Session = Depends(get_db)):
    return db.exec(select(VkBotSubscription)).all()

@router.post("/subscriptions", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
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
    sub.send_vk = data.send_vk
    sub.send_tg = data.send_tg
    sub.send_max = data.send_max
    sub.send_sms = data.send_sms
    
    db.add(sub)
    db.commit()
    return {"status": "success"}

@router.get("/accounts/{account_id}/subscriptions", response_model=List[VkBotSubscription], dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_account_subscriptions(account_id: int, db: Session = Depends(get_db)):
    return db.exec(select(VkBotSubscription).where(VkBotSubscription.account_id == account_id)).all()

@router.delete("/subscriptions/{subscription_id}", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    sub = db.get(VkBotSubscription, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    db.delete(sub)
    db.commit()
    return {"status": "success"}

COURIER_EVENT_TYPES = {
    "order_new", "courier_assigned", "change_cooking_time", 
    "order_status_update", "order_amount_changed", "order_items_changed", 
    "order_address_changed", "order_time_changed", "order_cancelled"
}

@router.get("/accounts/{account_id}/channel-settings", dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
async def get_account_channel_settings(account_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    from app.models.vk_bot_connection import VkBotConnection
    bot_connections = db.exec(select(VkBotConnection).where(VkBotConnection.is_active == True)).all()
    
    # 1. Проверка связи и авторизации сообщений по группам VK
    vk_groups_info = []
    for bot in bot_connections:
        is_allowed = False
        is_allowed_error = None
        if account.vk_user_id:
            try:
                chk = await vk_bot_service.is_messages_allowed(bot.vk_group_id, account.vk_user_id, bot_token_override=bot.vk_bot_token)
                if chk.get("success"):
                    is_allowed = chk.get("is_allowed", False)
                else:
                    is_allowed_error = chk.get("error")
            except Exception as e:
                is_allowed_error = str(e)
        else:
            is_allowed_error = "VK ID не привязан"

        vk_groups_info.append({
            "id": bot.id,
            "name": bot.name,
            "vk_group_id": bot.vk_group_id,
            "is_main": bot.is_main,
            "is_courier_bot": bool("курьер" in bot.name.lower() or bot.id == 2),
            "is_messages_allowed": is_allowed,
            "error": is_allowed_error,
            "allow_url": f"https://vk.com/im?sel=-{bot.vk_group_id}"
        })

    # 2. Настройки курьерских цепочек
    courier_bot = next((g for g in vk_groups_info if g.get("is_courier_bot")), None) or next((g for g in vk_groups_info if g.get("is_main")), None)
    courier_chains_info = {
        "allow_courier_chains": bool(getattr(account, "allow_courier_chains", True)),
        "is_courier": bool(account.is_courier),
        "send_vk": bool(getattr(account, "courier_chains_vk", account.use_vk)),
        "send_tg": bool(getattr(account, "courier_chains_tg", account.use_tg)),
        "send_max": bool(getattr(account, "courier_chains_max", account.use_max)),
        "send_sms": bool(getattr(account, "courier_chains_sms", account.use_sms)),
        "bot": courier_bot,
        "is_messages_allowed": courier_bot.get("is_messages_allowed", False) if courier_bot else False,
        "allow_url": courier_bot.get("allow_url") if courier_bot else None
    }

    # 3. Динамический список шаблонов для сотрудников из базы vk_templates (без курьерских цепочек!)
    all_templates = db.exec(select(VkTemplate).order_by(VkTemplate.id)).all()
    system_templates_db = [t for t in all_templates if t.event_type not in COURIER_EVENT_TYPES]
    
    account_subs = {s.event_type: s for s in db.exec(select(VkBotSubscription).where(VkBotSubscription.account_id == account_id)).all()}
    main_bot = next((g for g in vk_groups_info if g.get("is_main")), None) or (vk_groups_info[0] if vk_groups_info else None)

    templates_list = []
    for tpl in system_templates_db:
        sub = account_subs.get(tpl.event_type)
        is_sub = sub is not None
        
        target_bot_info = next((g for g in vk_groups_info if g["id"] == tpl.vk_bot_id), main_bot)
        
        is_vk_available = bool(account.vk_user_id and target_bot_info and target_bot_info.get("is_messages_allowed"))
        is_tg_available = bool(account.tg_user_id)
        is_max_available = bool(account.max_user_id or account.phone)
        
        availability_notes = []
        if tpl.send_vk and not is_vk_available:
            if not account.vk_user_id:
                availability_notes.append("Не привязан VK ID")
            elif target_bot_info and not target_bot_info.get("is_messages_allowed"):
                availability_notes.append(f"Требуется разрешение сообщений от «{target_bot_info.get('name')}»")
        if tpl.send_tg and not is_tg_available:
            availability_notes.append("Не привязан Telegram ID")
        if tpl.send_max and not is_max_available:
            availability_notes.append("Не привязан телефон/MAX ID")
            
        templates_list.append({
            "id": tpl.id,
            "name": tpl.name,
            "event_type": tpl.event_type,
            "description": tpl.description or "",
            "target_mode": tpl.target_mode or "all",
            "target_roles": tpl.target_roles,
            "target_accounts": tpl.target_accounts,
            "is_active": tpl.is_active,
            "vk_bot_id": tpl.vk_bot_id,
            "bot_name": target_bot_info.get("name") if target_bot_info else None,
            "bot_is_allowed": target_bot_info.get("is_messages_allowed") if target_bot_info else False,
            "bot_allow_url": target_bot_info.get("allow_url") if target_bot_info else None,
            "tpl_channels": {
                "vk": tpl.send_vk,
                "tg": tpl.send_tg,
                "max": tpl.send_max,
                "sms": tpl.send_sms
            },
            "subscribed": is_sub,
            "sub_channels": {
                "vk": sub.send_vk if sub else account.use_vk,
                "tg": sub.send_tg if sub else account.use_tg,
                "max": sub.send_max if sub else account.use_max,
                "sms": sub.send_sms if sub else account.use_sms
            },
            "delivery_mode": sub.delivery_mode if sub else "realtime",
            "interval_minutes": sub.interval_minutes if sub else 0,
            "active_start_hour": sub.active_start_hour if sub else 0,
            "active_end_hour": sub.active_end_hour if sub else 23,
            "is_available": is_vk_available or is_tg_available or is_max_available,
            "availability_notes": availability_notes
        })

    return {
        "account": {
            "id": account.id,
            "name": account.name,
            "phone": account.phone,
            "vk_user_id": account.vk_user_id,
            "tg_user_id": account.tg_user_id,
            "max_user_id": account.max_user_id,
            "use_vk": account.use_vk,
            "use_tg": account.use_tg,
            "use_max": account.use_max,
            "use_sms": account.use_sms,
            "is_active": account.is_active,
            "is_courier": account.is_courier
        },
        "vk_groups": vk_groups_info,
        "courier_chains": courier_chains_info,
        "system_templates": templates_list,
        "templates": templates_list
    }

@router.post("/accounts/{account_id}/check-vk-group/{bot_id}", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
async def check_account_vk_group(account_id: int, bot_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    if not account.vk_user_id:
        raise HTTPException(status_code=400, detail="VK ID не привязан")

    from app.models.vk_bot_connection import VkBotConnection
    bot = db.get(VkBotConnection, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот/сообщество не найдено")

    chk = await vk_bot_service.is_messages_allowed(bot.vk_group_id, account.vk_user_id, bot_token_override=bot.vk_bot_token)
    return {
        "status": "success",
        "group_id": bot.vk_group_id,
        "group_name": bot.name,
        "is_allowed": chk.get("is_allowed", False),
        "error": chk.get("error")
    }

@router.post("/accounts/{account_id}/send-test-vk-group/{bot_id}", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
async def send_test_vk_group(account_id: int, bot_id: int, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account or not account.vk_user_id:
        raise HTTPException(status_code=400, detail="Аккаунт или VK ID не найден")
    
    from app.models.vk_bot_connection import VkBotConnection
    bot = db.get(VkBotConnection, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот/сообщество не найдено")

    res = await vk_bot_service.send_message(
        user_id=account.vk_user_id,
        message=f"🔧 Проверка связи от сообщества «{bot.name}»! Доставка уведомлений FoodZuka настроена успешно.",
        account_id=account.id,
        event_type="test_connection",
        bot_token_override=bot.vk_bot_token
    )
    if res.get("success"):
        return {"status": "success", "message": f"Тестовое сообщение успешно отправлено от «{bot.name}»"}
    else:
        err = res.get("error") or "Ошибка отправки VK"
        if res.get("error_code") == 901:
            err = f"Пользователь не разрешил сообщения от группы «{bot.name}». Перейдите по ссылке https://vk.com/im?sel=-{bot.vk_group_id} и отправьте любое сообщение."
        return {"status": "error", "message": err}

@router.post("/accounts/{account_id}/toggle-courier-chains", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def toggle_account_courier_chains(account_id: int, data: CourierChainsToggleRequest, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    # Переключение общего флага цепочек курьера
    if data.allow_courier_chains is not None:
        account.allow_courier_chains = data.allow_courier_chains

    # Переключение отдельного канала цепочек (например channel="max", enabled=True)
    if data.channel and data.enabled is not None:
        ch = data.channel.lower().strip()
        if ch == 'vk': account.courier_chains_vk = data.enabled
        elif ch == 'tg': account.courier_chains_tg = data.enabled
        elif ch == 'max': account.courier_chains_max = data.enabled
        elif ch == 'sms': account.courier_chains_sms = data.enabled

    if data.send_vk is not None: account.courier_chains_vk = data.send_vk
    if data.send_tg is not None: account.courier_chains_tg = data.send_tg
    if data.send_max is not None: account.courier_chains_max = data.send_max
    if data.send_sms is not None: account.courier_chains_sms = data.send_sms
    db.add(account)

    from sqlalchemy import delete
    if account.allow_courier_chains is False:
        for ev in COURIER_EVENT_TYPES:
            db.execute(delete(VkBotSubscription).where(
                VkBotSubscription.account_id == account_id,
                VkBotSubscription.event_type == ev
            ))
    elif account.allow_courier_chains is True:
        for ev in COURIER_EVENT_TYPES:
            sub = db.exec(select(VkBotSubscription).where(
                VkBotSubscription.account_id == account_id,
                VkBotSubscription.event_type == ev
            )).first()
            if not sub:
                sub = VkBotSubscription(
                    account_id=account_id,
                    event_type=ev,
                    delivery_mode=DeliveryMode.REALTIME,
                    active_start_hour=0,
                    active_end_hour=23,
                    send_vk=bool(account.courier_chains_vk),
                    send_tg=bool(account.courier_chains_tg),
                    send_max=bool(account.courier_chains_max),
                    send_sms=bool(account.courier_chains_sms)
                )
            else:
                sub.send_vk = bool(account.courier_chains_vk)
                sub.send_tg = bool(account.courier_chains_tg)
                sub.send_max = bool(account.courier_chains_max)
                sub.send_sms = bool(account.courier_chains_sms)
            db.add(sub)

    db.commit()
    return {
        "status": "success", 
        "allow_courier_chains": account.allow_courier_chains,
        "courier_chains_vk": account.courier_chains_vk,
        "courier_chains_tg": account.courier_chains_tg,
        "courier_chains_max": account.courier_chains_max,
        "courier_chains_sms": account.courier_chains_sms
    }

@router.post("/accounts/{account_id}/toggle-template-subscription", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def toggle_template_subscription(account_id: int, data: TemplateSubscriptionToggleRequest, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    tpl = None
    if data.template_id:
        tpl = db.get(VkTemplate, data.template_id)
    elif data.event_type:
        tpl = db.exec(select(VkTemplate).where(VkTemplate.event_type == data.event_type)).first()
    
    target_event_type = tpl.event_type if tpl else data.event_type
    if not target_event_type:
        raise HTTPException(status_code=404, detail="Шаблон или тип события не найден")

    from sqlalchemy import delete
    if data.subscribed is False:
        db.execute(delete(VkBotSubscription).where(
            VkBotSubscription.account_id == account_id,
            VkBotSubscription.event_type == target_event_type
        ))
        db.commit()
        return {"status": "success", "subscribed": False}

    sub = db.exec(select(VkBotSubscription).where(
        VkBotSubscription.account_id == account_id,
        VkBotSubscription.event_type == target_event_type
    )).first()

    if not sub:
        sub = VkBotSubscription(
            account_id=account_id,
            event_type=target_event_type
        )

    if data.channel:
        ch = data.channel.lower().strip()
        val = data.enabled if data.enabled is not None else True
        if ch == "vk": sub.send_vk = val
        elif ch == "tg": sub.send_tg = val
        elif ch == "max": sub.send_max = val
        elif ch == "sms": sub.send_sms = val

    if data.send_vk is not None: sub.send_vk = data.send_vk
    if data.send_tg is not None: sub.send_tg = data.send_tg
    if data.send_max is not None: sub.send_max = data.send_max
    if data.send_sms is not None: sub.send_sms = data.send_sms
    if data.delivery_mode: sub.delivery_mode = data.delivery_mode
    if data.interval_minutes is not None: sub.interval_minutes = data.interval_minutes
    if data.active_start_hour is not None: sub.active_start_hour = data.active_start_hour
    if data.active_end_hour is not None: sub.active_end_hour = data.active_end_hour

    db.add(sub)
    db.commit()
    return {"status": "success", "subscribed": True}

@router.post("/accounts/{account_id}/bulk-toggle-templates", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def bulk_toggle_templates(account_id: int, data: BulkTemplatesToggleRequest, db: Session = Depends(get_db)):
    account = db.get(VkBotAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    all_templates = db.exec(select(VkTemplate)).all()
    system_templates_db = [t for t in all_templates if t.event_type not in COURIER_EVENT_TYPES and t.event_type]

    from sqlalchemy import delete
    if data.action == "disable_all":
        for tpl in system_templates_db:
            db.execute(delete(VkBotSubscription).where(
                VkBotSubscription.account_id == account_id,
                VkBotSubscription.event_type == tpl.event_type
            ))
    elif data.action == "enable_all":
        for tpl in system_templates_db:
            sub = db.exec(select(VkBotSubscription).where(
                VkBotSubscription.account_id == account_id,
                VkBotSubscription.event_type == tpl.event_type
            )).first()
            if not sub:
                sub = VkBotSubscription(
                    account_id=account_id,
                    event_type=tpl.event_type,
                    delivery_mode=DeliveryMode.REALTIME,
                    active_start_hour=0,
                    active_end_hour=23,
                    send_vk=account.use_vk,
                    send_tg=account.use_tg,
                    send_max=account.use_max,
                    send_sms=account.use_sms
                )
                db.add(sub)
    elif data.action in ("set_channel", "channel") and data.channel:
        ch = data.channel.lower().strip()
        val = bool(data.value) if data.value is not None else True
        for tpl in system_templates_db:
            sub = db.exec(select(VkBotSubscription).where(
                VkBotSubscription.account_id == account_id,
                VkBotSubscription.event_type == tpl.event_type
            )).first()
            if not sub and val:
                sub = VkBotSubscription(
                    account_id=account_id,
                    event_type=tpl.event_type,
                    delivery_mode=DeliveryMode.REALTIME,
                    active_start_hour=0,
                    active_end_hour=23,
                    send_vk=(ch == "vk"),
                    send_tg=(ch == "tg"),
                    send_max=(ch == "max"),
                    send_sms=(ch == "sms")
                )
                db.add(sub)
            elif sub:
                if ch == "vk": sub.send_vk = val
                elif ch == "tg": sub.send_tg = val
                elif ch == "max": sub.send_max = val
                elif ch == "sms": sub.send_sms = val
                db.add(sub)

    db.commit()
    return {"status": "success"}

# --- Шаблоны ---

@router.get("/templates", response_model=List[VkTemplate], dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_templates(db: Session = Depends(get_db)):
    # Проверяем и создаем дефолтные шаблоны для системных событий и цепочек курьера
    available_events = {
        "order_new_all": (
            "Новый заказ (любой)", 
            "🔔 Поступил новый заказ #{{order.external_number}}\nСумма: {{order.total_with_discount}} руб.\nТип: {{order.order_type}}\nКлиент: {{order.customer_name}} (тел: {{order.customer_phone}})\nАдрес: {{order.address}}\n\nСостав заказа:\n{{order.items_summary}}",
            "all",
            None,
            False,
            "Общее уведомление при поступлении любого нового заказа (доставка, самовывоз, зал)"
        ),
        "order_new": (
            "Новый заказ курьеру", 
            "🔔 Новый заказ #{{order.external_number}}\nСумма: {{order.total_with_discount}} руб.\nКлиент: {{order.customer_name}} (тел: {{order.customer_phone}})\nТип: {{order.order_type}}\nАдрес: {{order.address}}\nПримечание: {{order.address_comment}}\nПодъезд: {{order.entrance}}, Этаж: {{order.floor}}, Домофон: {{order.doorphone}}\nВремя доставки: {{order.delivery_time}}\nКомментарий: {{order.comment}}\n\nСостав заказа:\n{{order.items_summary}}",
            "assigned_only",
            None,
            True,
            "Уведомление назначенному курьеру при поступлении нового заказа с составом и QR СБП"
        ),
        "order_status_update": (
            "Статус заказа", 
            "🔔 Статус заказа #{{order.external_number}} изменен на «{{order.status}}»\nКурьер: {{order.courier_name}}\nАдрес: {{order.address}}\nСумма к оплате: {{order.total_with_discount}} руб.",
            "assigned_only",
            '["cooking", "ready_for_pickup", "delivering", "delivered", "cancelled"]',
            False,
            "Уведомление курьеру при переходе заказа в один из выбранных статусов"
        ),
        "order_amount_changed": (
            "Изменение суммы", 
            "🔔 Внимание! Изменилась сумма заказа #{{order.external_number}}\nНовая сумма к оплате: {{order.total_with_discount}} руб.\nАдрес: {{order.address}}\nКлиент: {{order.customer_name}}",
            "assigned_only",
            None,
            False,
            "Уведомление курьеру при изменении суммы к оплате или скидки"
        ),
        "order_items_changed": (
            "Изменение состава", 
            "🔔 Состав заказа #{{order.external_number}} изменен.\nНовый состав:\n{{order.items_summary}}",
            "assigned_only",
            None,
            False,
            "Уведомление курьеру при корректировке блюд в заказе"
        ),
        "order_time_changed": (
            "Изменение времени доставки", 
            "🔔 Ожидаемое время доставки заказа #{{order.external_number}} изменено на {{order.delivery_time}}\nАдрес: {{order.address}}",
            "assigned_only",
            None,
            False,
            "Уведомление курьеру при переносе времени доставки клиенту"
        ),
        "order_address_changed": (
            "Изменение адреса доставки", 
            "🔔 Внимание! Изменен адрес доставки заказа #{{order.external_number}}\nНовый адрес: {{order.address}}\nПримечание: {{order.address_comment}}\nПодъезд: {{order.entrance}}, Этаж: {{order.floor}}, Домофон: {{order.doorphone}}\nКурьер: {{order.courier_name}}",
            "assigned_only",
            None,
            False,
            "Уведомление курьеру при изменении адреса или деталей доставки"
        ),
        "order_cancelled": (
            "Отмена заказа", 
            "🔔 Заказ #{{order.external_number}} ОТМЕНЕН! Доставка отменена.",
            "assigned_only",
            None,
            False,
            "Срочное уведомление курьеру об отмене заказа"
        ),
        "shift_open": (
            "Открытие смены", 
            "👤 Смена ОТКРЫТА\nСотрудник: {{employee.name}}\nРоль: {{employee.role}}\nНачало: {{shift.date_open}}",
            "all",
            None,
            False,
            "Уведомление об открытии рабочей смены"
        ),
        "shift_close": (
            "Закрытие смены", 
            "👤 Смена ЗАКРЫТА\nСотрудник: {{employee.name}}\nРоль: {{employee.role}}\nКонец: {{shift.date_close}}\nОтработано: {{shift.work_hours}} ч.\nВыручка: {{shift.revenue_at_close}} руб.",
            "all",
            None,
            False,
            "Уведомление с итогами закрытия смены"
        ),
        "bonus_order": (
            "Заказ за баллы", 
            "🔔 Оформлен заказ за баллы #{{order.external_number}}",
            "all",
            None,
            False,
            "Уведомление об оформлении заказа за баллы"
        ),
        "system_alert": (
            "Системный алерт", 
            "⚠️ Системное предупреждение!",
            "all",
            None,
            False,
            "Важные системные предупреждения администраторам"
        ),
        "courier_assigned": (
            "Назначение курьера", 
            "🔔 Вам назначен заказ #{{order.external_number}}!\nСумма: {{order.total_with_discount}} руб.\nАдрес: {{order.address}}\nПримечание: {{order.address_comment}}\nПодъезд: {{order.entrance}}, Этаж: {{order.floor}}, Домофон: {{order.doorphone}}\nВремя доставки: {{order.delivery_time}}\nКомментарий: {{order.comment}}\n\nСостав заказа:\n{{order.items_summary}}",
            "assigned_only",
            None,
            True,
            "Адресное уведомление курьеру о назначении на доставку с подробностями и QR СБП"
        ),
        "change_cooking_time": (
            "Время готовности на кухне", 
            "👨‍🍳 Заказ #{{order.external_number}}: время приготовления {{order.cooking_time_minutes}} мин.\n\n⏰ Прибыть за заказом к: {{order.pickup_time}} (установлено в {{order.cooking_set_time}})\n📍 Адрес: {{order.address}}\nСтатус: {{order.status}}",
            "assigned_only",
            None,
            False,
            "Уведомление курьеру при установке или изменении времени приготовления на кухне"
        ),
        "purchase_list_sent": (
            "Отправка списка закупа", 
            "📦 Отправлен список закупа: {{purchase_list.name}}\nНаправление: {{purchase_list.category_name}}\nДата поставки: {{purchase_list.date}}\n\nПозиции к закупу:\n{{purchase_list.items_summary}}",
            "all",
            None,
            False,
            "Уведомление сотрудникам о сформированном списке закупа"
        )
    }
    
    updated = False
    for event_id, item in available_events.items():
        name = item[0]
        def_text = item[1]
        target_mode = item[2]
        inc_statuses = item[3]
        attach_qr = item[4]
        desc = item[5]

        existing = db.exec(select(VkTemplate).where(VkTemplate.event_type == event_id)).first()
        if not existing:
            new_tpl = VkTemplate(
                name=f"[Системный] {name}",
                text=def_text,
                event_type=event_id,
                target_mode=target_mode,
                is_active=True,
                include_statuses=inc_statuses,
                attach_sbp_qr=attach_qr,
                description=desc
            )
            db.add(new_tpl)
            updated = True
        else:
            # Если поле include_statuses еще не заполнено для смены статуса, обновляем
            if event_id == "order_status_update" and not existing.include_statuses:
                existing.include_statuses = inc_statuses
                existing.description = desc
                db.add(existing)
                updated = True
            elif not existing.description and desc:
                existing.description = desc
                db.add(existing)
                updated = True
                
            if not existing.chain_config:
                if event_id in ("order_new", "courier_assigned"):
                    existing.chain_config = '{"require_courier_assigned": true, "resend_on_courier_reassigned": true, "attach_sbp_qr": true, "only_unpaid": false}'
                elif event_id == "change_cooking_time":
                    existing.chain_config = '{"require_courier_assigned": true, "require_cooking_time_set": true, "require_cooking_time_changed": true}'
                elif event_id == "order_status_update":
                    existing.chain_config = '{"require_courier_assigned": true, "check_status_in": ["cooking", "ready_for_pickup", "delivering", "cancelled"]}'
                elif event_id == "order_amount_changed":
                    existing.chain_config = '{"require_courier_assigned": true, "require_amount_changed": true}'
                elif event_id == "order_address_changed":
                    existing.chain_config = '{"require_courier_assigned": true, "require_address_changed": true}'
                elif event_id == "order_time_changed":
                    existing.chain_config = '{"require_courier_assigned": true, "require_time_changed": true}'
                db.add(existing)
                updated = True
            
    if updated:
        db.commit()
        
    return db.exec(select(VkTemplate).order_by(VkTemplate.id)).all()

@router.get("/templates/{template_id}", response_model=VkTemplate, dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return template

def clean_template_data(data_dict: dict) -> dict:
    for key in ["keyboard_json", "keyboard_telegram", "keyboard_max", "event_type", "include_statuses", "chain_config", "description"]:
        if key in data_dict:
            val = data_dict[key]
            if val == "" or (isinstance(val, str) and not val.strip()):
                data_dict[key] = None
    if "target_mode" in data_dict:
        if not data_dict["target_mode"]:
            data_dict["target_mode"] = "all"
    import json
    if "target_roles" in data_dict:
        val = data_dict["target_roles"]
        if val is None or val == "":
            data_dict["target_roles"] = None
        elif isinstance(val, list):
            data_dict["target_roles"] = json.dumps(val, ensure_ascii=False) if val else None
    if "target_accounts" in data_dict:
        val = data_dict["target_accounts"]
        if val is None or val == "":
            data_dict["target_accounts"] = None
        elif isinstance(val, list):
            data_dict["target_accounts"] = json.dumps(val, ensure_ascii=False) if val else None
    if "vk_bot_id" in data_dict:
        try:
            val = data_dict["vk_bot_id"]
            if val is None or val == "" or int(val) <= 0:
                data_dict["vk_bot_id"] = None
            else:
                data_dict["vk_bot_id"] = int(val)
        except (ValueError, TypeError):
            data_dict["vk_bot_id"] = None
    return data_dict

@router.post("/templates", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def create_template(data: VkTemplateCreate, db: Session = Depends(get_db)):
    cleaned_data = clean_template_data(data.dict())
    template = VkTemplate(**cleaned_data)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.patch("/templates/{template_id}", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def update_template(template_id: int, data: VkTemplateUpdate, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    cleaned_data = clean_template_data(data.dict(exclude_unset=True))
    for key, value in cleaned_data.items():
        setattr(template, key, value)
    
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.post("/templates/{template_id}/toggle-channel", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def toggle_template_channel(template_id: int, data: ChannelToggleRequest, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    ch = data.channel.lower()
    if ch == "vk":
        template.send_vk = data.enabled
    elif ch == "tg":
        template.send_tg = data.enabled
    elif ch == "max":
        template.send_max = data.enabled
    elif ch == "sms":
        template.send_sms = data.enabled
    else:
        raise HTTPException(status_code=400, detail="Неверный канал")
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"status": "success", "template_id": template_id, "channel": ch, "enabled": data.enabled}

@router.post("/templates/{template_id}/set-bot", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def set_template_bot(template_id: int, data: TemplateBotSetRequest, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    bot_id = data.vk_bot_id if (data.vk_bot_id and data.vk_bot_id > 0) else None
    template.vk_bot_id = bot_id
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"status": "success", "template_id": template_id, "vk_bot_id": bot_id}

@router.post("/templates/{template_id}/set-max-bot", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def set_template_max_bot(template_id: int, data: TemplateMaxBotSetRequest, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    bot_id = data.max_bot_id if (data.max_bot_id and data.max_bot_id > 0) else None
    template.max_bot_id = bot_id
    if data.max_send_mode:
        template.max_send_mode = data.max_send_mode
    db.add(template)
    db.commit()
    db.refresh(template)
    return {
        "status": "success", 
        "template_id": template_id, 
        "max_bot_id": bot_id, 
        "max_send_mode": template.max_send_mode
    }

@router.get("/max-bots", dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_max_bots(db: Session = Depends(get_db)):
    """Получение списка активных ботов MAX для системных рассылок"""
    from app.models.max_settings import MaxBot
    bots = db.exec(select(MaxBot).where(MaxBot.is_active == True)).all()
    return [
        {
            "id": b.id,
            "bot_name": b.bot_name,
            "bot_username": b.bot_username,
            "bot_external_id": b.bot_external_id,
            "is_default_for_notifications": bool(b.is_default_for_notifications)
        }
        for b in bots
    ]

@router.post("/templates/bulk-toggle-chains", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def bulk_toggle_chains(data: BulkChainsToggleRequest, db: Session = Depends(get_db)):
    courier_events = [
        'order_new', 'courier_assigned', 'change_cooking_time', 
        'order_status_update', 'order_amount_changed', 'order_address_changed', 
        'order_time_changed', 'order_cancelled'
    ]
    templates = db.exec(select(VkTemplate).where(VkTemplate.event_type.in_(courier_events))).all()
    for t in templates:
        t.is_active = data.enabled
        db.add(t)
    db.commit()
    return {"status": "success", "count": len(templates), "enabled": data.enabled}

@router.delete("/templates/{template_id}", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.get(VkTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    db.delete(template)
    db.commit()
    return {"status": "success"}

class BulkTemplatesDeleteRequest(BaseModel):
    template_ids: List[int]

class BulkTemplatesChannelsRequest(BaseModel):
    template_ids: List[int]
    send_vk: Optional[bool] = None
    send_tg: Optional[bool] = None
    send_max: Optional[bool] = None
    send_sms: Optional[bool] = None

class BulkTemplatesBotRequest(BaseModel):
    template_ids: List[int]
    vk_bot_id: Optional[int] = None

class BulkTemplatesStatusRequest(BaseModel):
    template_ids: List[int]
    is_active: bool

class TemplateTestSendRequest(BaseModel):
    recipient_account_id: Optional[int] = None

@router.post("/templates/{template_id}/toggle-active", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def toggle_template_active(template_id: int, db: Session = Depends(get_db)):
    tpl = db.get(VkTemplate, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    tpl.is_active = not bool(tpl.is_active)
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return {"status": "success", "template_id": template_id, "is_active": tpl.is_active}

@router.post("/templates/bulk-delete", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def bulk_delete_templates(data: BulkTemplatesDeleteRequest, db: Session = Depends(get_db)):
    if not data.template_ids:
        return {"status": "success", "count": 0}
    deleted = 0
    for tid in data.template_ids:
        tpl = db.get(VkTemplate, tid)
        if tpl:
            db.delete(tpl)
            deleted += 1
    db.commit()
    return {"status": "success", "count": deleted}

@router.post("/templates/bulk-channels", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def bulk_update_template_channels(data: BulkTemplatesChannelsRequest, db: Session = Depends(get_db)):
    if not data.template_ids:
        return {"status": "success", "count": 0}
    updated = 0
    for tid in data.template_ids:
        tpl = db.get(VkTemplate, tid)
        if tpl:
            if data.send_vk is not None:
                tpl.send_vk = data.send_vk
            if data.send_tg is not None:
                tpl.send_tg = data.send_tg
            if data.send_max is not None:
                tpl.send_max = data.send_max
            if data.send_sms is not None:
                tpl.send_sms = data.send_sms
            db.add(tpl)
            updated += 1
    db.commit()
    return {"status": "success", "count": updated}

@router.post("/templates/bulk-bot", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def bulk_update_template_bot(data: BulkTemplatesBotRequest, db: Session = Depends(get_db)):
    if not data.template_ids:
        return {"status": "success", "count": 0}
    bot_id = data.vk_bot_id if (data.vk_bot_id and data.vk_bot_id > 0) else None
    updated = 0
    for tid in data.template_ids:
        tpl = db.get(VkTemplate, tid)
        if tpl:
            tpl.vk_bot_id = bot_id
            db.add(tpl)
            updated += 1
    db.commit()
    return {"status": "success", "count": updated}

@router.post("/templates/bulk-status", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
def bulk_update_template_status(data: BulkTemplatesStatusRequest, db: Session = Depends(get_db)):
    if not data.template_ids:
        return {"status": "success", "count": 0}
    updated = 0
    for tid in data.template_ids:
        tpl = db.get(VkTemplate, tid)
        if tpl:
            tpl.is_active = data.is_active
            db.add(tpl)
            updated += 1
    db.commit()
    return {"status": "success", "count": updated}

@router.post("/templates/{template_id}/test-send", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
async def test_send_template(template_id: int, data: TemplateTestSendRequest, db: Session = Depends(get_db)):
    from app.services.vk_notification_router import vk_notification_router
    from app.models.order import Order
    tpl = db.get(VkTemplate, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    sample_order = db.exec(select(Order).order_by(Order.id.desc()).limit(1)).first()
    context = {}
    if sample_order:
        order_dict = {
            "id": sample_order.id,
            "external_number": sample_order.external_number or str(sample_order.id),
            "customer_name": sample_order.customer_name or "Тестовый Клиент",
            "customer_phone": sample_order.customer_phone or "+79990000000",
            "delivery_address": sample_order.delivery_address or "г. Тюмень, ул. Республики, д. 1",
            "order_type": sample_order.order_type or "Доставка",
            "total_with_discount": float(sample_order.total_with_discount or sample_order.total_amount or 1500),
            "total_amount": float(sample_order.total_amount or 1500),
            "comment": sample_order.comment or "Тестовый заказ для проверки шаблона",
            "courier_name": sample_order.courier_name or "Сергей Тест",
            "cooking_time_minutes": 15,
            "cooking_time": "15 мин.",
            "pickup_time": "18:45",
            "delivery_time": "19:15",
            "entrance": sample_order.entrance or "1",
            "floor": sample_order.floor or "3",
            "doorphone": sample_order.doorphone or "15",
            "items_summary": "1x Фирменный ролл Сяке Маки\n1x Сет Запеченный Люкс"
        }
        context["order"] = order_dict
        context["customer"] = sample_order.customer if hasattr(sample_order, 'customer') else None
    
    rendered = vk_notification_router.render_template(tpl.text, context)
    
    target_acc = None
    if data.recipient_account_id:
        target_acc = db.get(VkBotAccount, data.recipient_account_id)
    if not target_acc:
        target_acc = db.exec(select(VkBotAccount).where(VkBotAccount.is_active == True, VkBotAccount.use_vk == True, VkBotAccount.vk_user_id != None)).first()
        
    if not target_acc:
        return {"status": "error", "rendered_text": rendered, "detail": "Нет подходящего активного аккаунта с VK ID для тестовой отправки"}
        
    from app.services.vk_bot_service import vk_bot_service
    from app.models.vk_bot_connection import VkBotConnection
    bot_token = None
    if tpl.vk_bot_id:
        b = db.get(VkBotConnection, tpl.vk_bot_id)
        if b:
            bot_token = b.vk_bot_token
            
    res = await vk_bot_service.send_message(
        user_id=target_acc.vk_user_id,
        message=f"🧪 [ТЕСТ ШАБЛОНА: {tpl.name}]\n\n{rendered}",
        keyboard=tpl.keyboard_json,
        bot_token_override=bot_token
    )
    is_ok = bool(res.get("response") or res.get("success"))
    return {
        "status": "success" if is_ok else "failed",
        "rendered_text": rendered,
        "recipient": target_acc.name,
        "vk_user_id": target_acc.vk_user_id,
        "vk_response": res
    }

@router.get("/roles", dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_roles(db: Session = Depends(get_db)):
    """Получение списка уникальных должностей и ролей сотрудников для адресации"""
    from app.models.employee import Employee
    from app.models.vk_bot import VkBotGroup
    roles = set()
    emp_roles = db.exec(select(Employee.role).where(Employee.role != None, Employee.role != "")).all()
    for r in emp_roles:
        if r and str(r).strip():
            roles.add(str(r).strip())
    group_names = db.exec(select(VkBotGroup.name)).all()
    for g in group_names:
        if g and str(g).strip():
            roles.add(str(g).strip())
    for default_role in ["Курьер", "Повар", "Администратор", "Менеджер", "Оператор"]:
        roles.add(default_role)
    return sorted(list(roles))

@router.post("/preview-sbp-qr", dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
async def preview_sbp_qr(
    data: SbpQrPreviewRequest,
    db: Session = Depends(get_db)
):
    """Генерация тестового образца QR-кода СБП с надписями для предпросмотра в админке"""
    from app.services.vk_notification_router import generate_sbp_qr_image
    import os
    img_path = await generate_sbp_qr_image(
        order_id=99999,
        amount=data.amount,
        session=db,
        order_number=data.order_number or "104",
        delivery_address=data.delivery_address or "г. Тюмень, ул. Республики, д. 142, кв. 15"
    )
    if not img_path:
        raise HTTPException(status_code=500, detail="Не удалось сгенерировать превью QR-кода")
        
    filename = os.path.basename(img_path)
    return {
        "status": "success",
        "url": f"/media/img/qr/{filename}",
        "full_url": f"https://vezuroll.ru/media/img/qr/{filename}"
    }

@router.get("/variables", dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_template_variables(db: Session = Depends(get_db)):
    """Возвращает список доступных переменных, типов событий и активных команд бота"""
    from app.models.bot_command import BotCommand
    bot_commands = db.exec(select(BotCommand).where(BotCommand.is_active == True)).all()
    commands_list = [{"trigger": cmd.trigger_phrase, "name": cmd.name} for cmd in bot_commands]
    
    return {
        "variables": {
            "Заказ (order)": {
                "order.external_number": "Номер заказа (из iiko)",
                "order.order_number": "Номер заказа (синоним)",
                "order.total_amount": "Сумма без скидки",
                "order.total_with_discount": "Итоговая сумма (к оплате)",
                "order.final_price": "Итоговая сумма (к оплате) - синоним",
                "order.total_discount": "Сумма скидки",
                "order.discount_sum": "Сумма скидки - синоним",
                "order.items_summary": "Состав заказа с ценами (полный)",
                "order.customer_name": "Имя гостя",
                "order.customer_phone": "Телефон гостя",
                "order.address": "Адрес доставки",
                "order.delivery_address": "Адрес доставки (синоним)",
                "order.address_comment": "Примечание к адресу (из iiko)",
                "order.entrance": "Подъезд",
                "order.floor": "Этаж",
                "order.doorphone": "Домофон",
                "order.delivery_time": "Время доставки (ожидаемое)",
                "order.comment": "Комментарий клиента/оператора к заказу",
                "order.courier_notes": "Служебные пометки и заметки курьеру из iiko",
                "order.additional_info": "Дополнительная информация из iiko",
                "order.courier_name": "Имя назначенного курьера",
                "order.status": "Статус заказа (текущий)",
                "order.old_status": "Предыдущий статус заказа",
                "order.cooking_time_minutes": "Время готовности на кухне (минуты)",
                "order.cooking_time": "Время готовности (синоним)",
                "order.cooking_set_time": "Время установки готовности (ЧЧ:ММ местное)",
                "order.cooking_updated_at": "Дата и время установки (ДД.ММ ЧЧ:ММ)",
                "order.pickup_time": "Время прибытия за заказом / готовности (ЧЧ:ММ местное)",
                "order.arrival_time": "Время прибытия курьера (синоним)",
                "order.ready_time": "Время готовности (синоним)",
                "order.payment_method": "Способ оплаты",
                "order.sbp_qr_url": "Ссылка на изображение QR-кода оплаты по СБП",
                "order.sbp_pay_link": "Прямая ссылка для оплаты по СБП (NSPK deeplink)",
                "order.map_yandex": "Ссылка на Яндекс.Карты",
                "order.map_2gis": "Ссылка на 2ГИС",
            },
            "Клиент (customer)": {
                "customer.name": "Имя в базе",
                "customer.phone": "Телефон",
                "customer.bonus_points": "Баланс бонусов",
                "customer.categories": "Категории (метки) клиента",
                "customer.notes": "Заметки о клиенте"
            },
            "Смена (shift)": {
                "shift.date_open": "Время открытия смены",
                "shift.date_close": "Время закрытия смены",
                "shift.work_hours": "Отработанные часы",
                "shift.deliveries_count": "Количество доставок",
                "shift.deliveries_revenue": "Выручка за доставки",
                "shift.cancelled_orders_count": "Количество отмененных заказов",
                "shift.revenue_at_close": "Выручка на момент закрытия (общая)",
                "shift.kitchen_revenue": "Выручка цеха Кухня",
                "shift.hot_revenue": "Выручка Горячего цеха"
            },
            "Сотрудник (employee)": {
                "employee.name": "Имя сотрудника",
                "employee.phone": "Телефон сотрудника",
                "employee.role": "Роль/должность в iiko"
            },
            "Список закупа (purchase_list)": {
                "purchase_list.name": "Название списка закупа",
                "purchase_list.category_name": "Направление (Магазин, Хозка, Поставки)",
                "purchase_list.date": "Дата поставки (ДД.ММ.ГГГГ)",
                "purchase_list.items_summary": "Сводка товаров по категориям"
            }
        },
        "events": [
            {"type": "order_new_all", "name": "Новый заказ (любой: доставка/самовывоз/зал)"},
            {"type": "order_new", "name": "Новый заказ на доставку"},
            {"type": "order_status_update", "name": "Изменение статуса заказа"},
            {"type": "order_amount_changed", "name": "Изменение суммы заказа"},
            {"type": "order_items_changed", "name": "Изменение состава блюд"},
            {"type": "order_time_changed", "name": "Изменение времени доставки"},
            {"type": "order_address_changed", "name": "Изменение адреса доставки"},
            {"type": "courier_assigned", "name": "Назначение курьера"},
            {"type": "change_cooking_time", "name": "Время готовности на кухне"},
            {"type": "order_cancelled", "name": "Отмена заказа"},
            {"type": "shift_open", "name": "Открытие смены"},
            {"type": "shift_close", "name": "Закрытие смены"},
            {"type": "bonus_order", "name": "Заказ за баллы"},
            {"type": "system_alert", "name": "Системный алерт"},
            {"type": "purchase_list_sent", "name": "Отправка списка закупа"}
        ],
        "bot_commands": commands_list
    }

# --- Рассылки ---

@router.post("/broadcast", dependencies=[Depends(require_permission("settings_vk_notifications_edit"))])
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

@router.get("/logs", dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_logs(limit: int = 50, db: Session = Depends(get_db)):
    statement = select(VkBotMessageLog).order_by(VkBotMessageLog.created_at.desc()).limit(limit)
    return db.exec(statement).all()

# --- Группы ---

@router.get("/groups", response_model=List[VkBotGroup], dependencies=[Depends(require_permission("settings_vk_notifications_view"))])
def get_groups(db: Session = Depends(get_db)):
    return db.exec(select(VkBotGroup)).all()
