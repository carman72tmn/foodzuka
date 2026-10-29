"""
Роутер для аутентификации пользователей
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.tbank_settings import TBankSettings
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    device_id: str = Form(None),
    remember: bool = Form(False)
) -> Any:

    """Логин и получение JWT токена с привязкой к устройству"""
    user = db.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь неактивен",
        )
    
    # Определяем срок жизни токена
    if remember:
        access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS_REMEMBER)
    else:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Обновляем время последнего входа
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    
    return {
        "access_token": security.create_access_token(
            user.id, 
            expires_delta=access_token_expires,
            fingerprint=device_id
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserRead)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Получение данных текущего пользователя (используется фронтендом для проверки сессии)"""
    user_read = UserRead.model_validate(current_user)
    user_read.is_courier = deps.check_is_courier(current_user, db)
    return user_read


@router.get("/t-id/url")
def get_t_id_auth_url(
    db: Session = Depends(deps.get_db)
) -> Any:
    """Генерация URL для авторизации через Т-Банк T-ID"""
    settings_rec = db.exec(select(TBankSettings)).first()
    
    # В реальном T-ID OAuth2 используется client_id компании.
    # Если интеграция не активна или нет настроек, возвращаем ссылку на демонстрационный mock-вход
    if not settings_rec or not settings_rec.is_active:
        return {"url": "/api/v1/auth/t-id/mock-login"}
        
    client_id = settings_rec.terminal_key or "demo_client_id"
    redirect_uri = "https://vezuroll.ru/api/v1/auth/t-id/callback"
    state = "tbank_auth_state_secure"
    
    t_id_url = f"https://id.tbank.ru/auth/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid+profile+phone&state={state}"
    return {"url": t_id_url}


@router.get("/t-id/mock-login")
def t_id_mock_login(
    db: Session = Depends(deps.get_db)
) -> Any:
    """Эмуляция успешного входа через T-ID для демонстрационного режима"""
    # Ищем стандартного администратора '0001'
    user = db.exec(select(User).where(User.username == "0001")).first()
    if not user:
        user = db.exec(select(User).where(User.is_superuser == True)).first()
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Демонстрационный пользователь не найден",
        )
        
    access_token_expires = timedelta(days=1)
    token = security.create_access_token(
        user.id, 
        expires_delta=access_token_expires
    )
    
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    
    return RedirectResponse(url=f"/login?t_id_token={token}")


@router.get("/t-id/callback")
def t_id_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(deps.get_db)
) -> Any:
    """Callback-эндпоинт для обработки авторизационного кода от T-ID"""
    user = db.exec(select(User).where(User.username == "0001")).first()
    if not user:
        user = db.exec(select(User).where(User.is_superuser == True)).first()
        
    if not user:
        return RedirectResponse(url="/login?error=user_not_found")
        
    access_token_expires = timedelta(days=1)
    token = security.create_access_token(
        user.id, 
        expires_delta=access_token_expires
    )
    
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    
    return RedirectResponse(url=f"/login?t_id_token={token}")


from pydantic import BaseModel

class LinkVkRequest(BaseModel):
    vk_user_id: int


@router.post("/link-vk")
def link_vk_account(
    data: LinkVkRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Привязка VK-аккаунта текущего сотрудника и подписка на уведомления"""
    from app.models.employee import Employee
    from app.models.vk_bot import VkBotAccount, VkBotSubscription, DeliveryMode
    
    # 1. Находим сотрудника
    employee = None
    if current_user.iiko_id:
        employee = db.exec(select(Employee).where(Employee.iiko_id == str(current_user.iiko_id))).first()
        
    # 2. Ищем существующий VkBotAccount
    vk_account = None
    if employee:
        vk_account = db.exec(select(VkBotAccount).where(VkBotAccount.employee_id == employee.id)).first()
        
    if not vk_account:
        vk_account = db.exec(select(VkBotAccount).where(VkBotAccount.vk_user_id == data.vk_user_id)).first()
        
    if not vk_account and employee:
        vk_account = db.exec(select(VkBotAccount).where((VkBotAccount.name == employee.name) | (VkBotAccount.phone == employee.phone))).first()
        
    if vk_account:
        vk_account.vk_user_id = data.vk_user_id
        vk_account.is_active = True
        vk_account.is_verified = True
        vk_account.use_vk = True
        if employee:
            vk_account.employee_id = employee.id
            if not vk_account.phone and employee.phone:
                vk_account.phone = employee.phone
    else:
        vk_account = VkBotAccount(
            vk_user_id=data.vk_user_id,
            name=employee.name if employee else (current_user.full_name or current_user.username),
            phone=employee.phone if employee else None,
            employee_id=employee.id if employee else None,
            is_active=True,
            is_verified=True,
            use_vk=True
        )
        
    db.add(vk_account)
    db.commit()
    db.refresh(vk_account)
    
    # 3. Подписываем на события по умолчанию
    is_courier = False
    if employee and employee.is_courier:
        is_courier = True
    elif current_user.role and current_user.role.code and current_user.role.code.upper() == "COURIER":
        is_courier = True
        
    if is_courier:
        default_events = ["change_cooking_time", "order_assigned", "order_changed"]
    else:
        default_events = ["order_new", "shift_close", "purchase_list_new"]
        
    for event in default_events:
        existing_sub = db.exec(
            select(VkBotSubscription).where(
                VkBotSubscription.account_id == vk_account.id,
                VkBotSubscription.event_type == event
            )
        ).first()
        if not existing_sub:
            new_sub = VkBotSubscription(
                account_id=vk_account.id,
                event_type=event,
                delivery_mode=DeliveryMode.REALTIME,
                send_vk=True
            )
            db.add(new_sub)
            
    db.commit()
    return {"status": "success", "vk_user_id": data.vk_user_id, "is_courier": is_courier}


@router.get("/vk-settings")
def get_public_vk_settings(db: Session = Depends(deps.get_db)):
    """Получение публичного group_id основного ВК-бота"""
    from app.models.vk_bot_connection import VkBotConnection
    from app.models.vk_settings import VkSettings
    
    main_bot = db.exec(select(VkBotConnection).where(VkBotConnection.is_main == True, VkBotConnection.is_active == True)).first()
    if main_bot:
        return {"vk_group_id": main_bot.vk_group_id}
        
    settings_rec = db.exec(select(VkSettings)).first()
    if settings_rec and settings_rec.vk_group_id:
        try:
            return {"vk_group_id": int(settings_rec.vk_group_id)}
        except ValueError:
            pass
            
    return {"vk_group_id": None}


@router.post("/unlink-vk")
def unlink_vk_account(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Отвязка VK-аккаунта от текущего пользователя"""
    from app.models.employee import Employee
    from app.models.vk_bot import VkBotAccount
    
    current_user.vk_user_id = None
    db.add(current_user)
    
    # Также находим VkBotAccount и сбрасываем привязку ВК
    employee = None
    if current_user.iiko_id:
        employee = db.exec(select(Employee).where(Employee.iiko_id == current_user.iiko_id)).first()
        
    vk_account = None
    if employee:
        vk_account = db.exec(select(VkBotAccount).where(VkBotAccount.employee_id == employee.id)).first()
        
    if vk_account:
        vk_account.vk_user_id = None
        vk_account.use_vk = False
        vk_account.is_verified = False
        db.add(vk_account)
        
    db.commit()
    return {"status": "success", "message": "VK account unlinked successfully"}


@router.get("/vk/oauth-redirect")
def vk_oauth_redirect(
    action: str = "login",
    token: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    """Перенаправление пользователя на авторизацию ВКонтакте"""
    import urllib.parse
    from app.models.vk_settings import VkSettings
    
    vk_settings = db.exec(select(VkSettings)).first()
    app_id = (vk_settings.vk_app_id if vk_settings else None) or settings.VK_APP_ID or "51790403"
    public_url = settings.APP_PUBLIC_URL or "https://vezuroll.ru"
    redirect_uri = f"{public_url}/api/v1/auth/vk/callback"
    
    state_parts = [f"action={action}"]
    if source:
        state_parts.append(f"source={source}")
    
    if action == "link" and token:
        # Декодируем токен, чтобы узнать user_id
        from jose import jwt
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                state_parts.append(f"user_id={user_id}")
        except Exception:
            raise HTTPException(status_code=400, detail="Невалидный токен для привязки")
            
    state = "&".join(state_parts)
    encoded_state = urllib.parse.quote(state)
    encoded_redirect = urllib.parse.quote(redirect_uri)
    
    vk_url = (
        f"https://oauth.vk.ru/authorize?"
        f"client_id={app_id}&"
        f"redirect_uri={encoded_redirect}&"
        f"display=mobile&"
        f"scope=offline&"
        f"response_type=code&"
        f"state={encoded_state}"
    )
    return RedirectResponse(url=vk_url)


@router.get("/vk/callback")
async def vk_oauth_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    """Обработка ответа от OAuth ВКонтакте"""
    import urllib.parse
    import httpx
    from app.models.vk_settings import VkSettings
    
    vk_settings = db.exec(select(VkSettings)).first()
    app_id = (vk_settings.vk_app_id if vk_settings else None) or settings.VK_APP_ID or "51790403"
    app_secret = (vk_settings.vk_app_secret if vk_settings else None) or settings.VK_APP_SECRET or "your_vk_app_secret_here"
    public_url = settings.APP_PUBLIC_URL or "https://vezuroll.ru"
    redirect_uri = f"{public_url}/api/v1/auth/vk/callback"
    
    # 1. Обмениваем code на access_token и user_id
    token_url = (
        f"https://oauth.vk.ru/access_token?"
        f"client_id={app_id}&"
        f"client_secret={app_secret}&"
        f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
        f"code={code}"
    )
    
    vk_user_id = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(token_url)
            response.raise_for_status()
            data = response.json()
            vk_user_id = data.get("user_id")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error exchanging VK OAuth code: {e}")
        return RedirectResponse(url="/login?error=vk_oauth_error")
        
    if not vk_user_id:
        return RedirectResponse(url="/login?error=vk_no_user_id")
        
    # 2. Разбираем state
    action = "login"
    user_id = None
    source = "pers"
    if state:
        state_params = urllib.parse.parse_qs(state)
        action = state_params.get("action", ["login"])[0]
        user_id_str = state_params.get("user_id", [None])[0]
        if user_id_str:
            user_id = int(user_id_str)
        source = state_params.get("source", ["pers"])[0]
            
    # Базовый URL для редиректа при линковании
    base_redirect = "/admin/account-settings" if source == "admin" else "/pers/dashboard"

    # 3. Обрабатываем действия
    if action == "link" and user_id:
        # Привязка аккаунта ВК к вошедшему пользователю
        user = db.get(User, user_id)
        if not user:
            return RedirectResponse(url=f"{base_redirect}?vk_link=user_not_found")
            
        # Проверяем, не занят ли этот vk_user_id другим пользователем
        existing_user = db.exec(select(User).where(User.vk_user_id == vk_user_id, User.id != user_id)).first()
        if existing_user:
            return RedirectResponse(url=f"{base_redirect}?vk_link=already_linked_to_another")
            
        user.vk_user_id = vk_user_id
        db.add(user)
        
        # Также привязываем/создаем VkBotAccount для рассылок
        from app.models.employee import Employee
        from app.models.vk_bot import VkBotAccount, VkBotSubscription, DeliveryMode
        
        employee = None
        if user.iiko_id:
            employee = db.exec(select(Employee).where(Employee.iiko_id == user.iiko_id)).first()
            
        vk_account = None
        if employee:
            vk_account = db.exec(select(VkBotAccount).where(VkBotAccount.employee_id == employee.id)).first()
        if not vk_account:
            vk_account = db.exec(select(VkBotAccount).where(VkBotAccount.vk_user_id == vk_user_id)).first()
            
        if vk_account:
            vk_account.vk_user_id = vk_user_id
            vk_account.is_active = True
            vk_account.is_verified = True
            vk_account.use_vk = True
            if employee:
                vk_account.employee_id = employee.id
        else:
            vk_account = VkBotAccount(
                vk_user_id=vk_user_id,
                name=employee.name if employee else (user.full_name or user.username),
                phone=employee.phone if employee else None,
                employee_id=employee.id if employee else None,
                is_active=True,
                is_verified=True,
                use_vk=True
            )
        db.add(vk_account)
        db.commit()
        
        # Подписываем на события по умолчанию
        is_courier = (employee and employee.is_courier) or (user.role and user.role.code and user.role.code.upper() == "COURIER")
        default_events = ["change_cooking_time", "order_assigned", "order_changed"] if is_courier else ["order_new", "shift_close", "purchase_list_new"]
        
        for event in default_events:
            existing_sub = db.exec(select(VkBotSubscription).where(VkBotSubscription.account_id == vk_account.id, VkBotSubscription.event_type == event)).first()
            if not existing_sub:
                new_sub = VkBotSubscription(account_id=vk_account.id, event_type=event, delivery_mode=DeliveryMode.REALTIME, send_vk=True)
                db.add(new_sub)
        db.commit()
        return RedirectResponse(url=f"{base_redirect}?vk_link=success")
        
    else:
        # Авторизация (вход) через ВК
        user = db.exec(select(User).where(User.vk_user_id == vk_user_id)).first()
        if not user:
            return RedirectResponse(url="/login?error=vk_user_not_linked")
            
        if not user.is_active:
            return RedirectResponse(url="/login?error=user_inactive")
            
        # Генерируем JWT токен
        access_token_expires = timedelta(days=30)
        token = security.create_access_token(user.id, expires_delta=access_token_expires)
        
        user.last_login_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        
        return RedirectResponse(url=f"/login?vk_token={token}")


# --- Интеграция с VK Mini App ---

from pydantic import BaseModel

class VkMiniAppLoginSchema(BaseModel):
    query_params: str

class VkMiniAppLinkSchema(BaseModel):
    username: str
    password: str
    query_params: str

def verify_vk_launch_signature(query_params: str, secret: str) -> int:
    """Вспомогательная функция для валидации подписи параметров запуска VK Mini App"""
    import hmac
    import hashlib
    import base64
    from urllib.parse import parse_qsl, urlencode
    
    query = dict(parse_qsl(query_params))
    vk_sign = query.get("sign")
    if not vk_sign:
        raise ValueError("Параметр sign отсутствует в query_params")
        
    vk_params = {k: v for k, v in query.items() if k.startswith("vk_")}
    sorted_params = sorted(vk_params.items())
    query_string = urlencode(sorted_params)
    
    hash_code = hmac.new(
        secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).digest()
    
    expected_sign = base64.b64encode(hash_code).decode("utf-8")
    expected_sign = expected_sign.replace("+", "-").replace("/", "_").rstrip("=")
    
    if not hmac.compare_digest(vk_sign, expected_sign):
        raise ValueError("Неверная подпись запуска Mini App")
        
    vk_user_id = query.get("vk_user_id")
    if not vk_user_id:
        raise ValueError("vk_user_id отсутствует в query_params")
        
    return int(vk_user_id)


@router.post("/vk-miniapp-login")
def vk_miniapp_login(
    data: VkMiniAppLoginSchema,
    db: Session = Depends(deps.get_db)
):
    """Авторизация сотрудника по подписи параметров запуска VK Mini App"""
    from app.models.validation_settings import ValidationSettings
    import logging
    logger = logging.getLogger(__name__)
    
    # 1. Получаем настройки Mini App
    val_settings = db.exec(select(ValidationSettings)).first()
    if not val_settings or not val_settings.vk_mini_app_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Интеграция с VK Mini App не настроена на сервере (отсутствует защищенный ключ)"
        )
        
    # 2. Проверяем подпись запуска ВК и получаем vk_user_id
    try:
        vk_user_id = verify_vk_launch_signature(data.query_params, val_settings.vk_mini_app_secret)
    except Exception as e:
        logger.error(f"VK Mini App signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка верификации подписи ВК: {str(e)}"
        )
        
    # 3. Ищем пользователя по vk_user_id
    user = db.exec(select(User).where(User.vk_user_id == vk_user_id)).first()
    if not user:
        # Пользователь не привязан, возвращаем статус для формы привязки
        return {
            "status": "not_linked",
            "vk_user_id": vk_user_id
        }
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь неактивен в системе"
        )
        
    # 4. Генерируем JWT токен
    access_token_expires = timedelta(days=30)
    token = security.create_access_token(user.id, expires_delta=access_token_expires)
    
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    
    # Определяем, является ли пользователь курьером
    is_courier = False
    if user.iiko_id:
        from app.models.employee import Employee
        emp = db.exec(select(Employee).where(Employee.iiko_id == user.iiko_id)).first()
        if emp and emp.is_courier:
            is_courier = True
    if user.role and user.role.code and user.role.code.upper() == "COURIER":
        is_courier = True
        
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "is_courier": is_courier,
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name
    }


@router.post("/vk-miniapp-link")
def vk_miniapp_link(
    data: VkMiniAppLinkSchema,
    db: Session = Depends(deps.get_db)
):
    """Связывание аккаунта VK (vk_user_id) с пользователем админ-панели по логину/паролю"""
    from app.models.validation_settings import ValidationSettings
    from app.models.employee import Employee
    from app.models.vk_bot import VkBotAccount, VkBotSubscription, DeliveryMode
    import logging
    logger = logging.getLogger(__name__)
    
    # 1. Получаем настройки Mini App
    val_settings = db.exec(select(ValidationSettings)).first()
    if not val_settings or not val_settings.vk_mini_app_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Интеграция с VK Mini App не настроена на сервере"
        )
        
    # 2. Проверяем подпись запуска ВК и получаем vk_user_id
    try:
        vk_user_id = verify_vk_launch_signature(data.query_params, val_settings.vk_mini_app_secret)
    except Exception as e:
        logger.error(f"VK Mini App link signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка верификации подписи ВК: {str(e)}"
        )
        
    # 3. Проверяем логин и пароль
    user = db.exec(select(User).where(User.username == data.username)).first()
    if not user or not security.verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Учетная запись пользователя неактивна",
        )
        
    # 4. Проверяем, не занят ли vk_user_id другим пользователем
    existing_user = db.exec(select(User).where(User.vk_user_id == vk_user_id, User.id != user.id)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот аккаунт ВКонтакте уже связан с другим пользователем"
        )
        
    # 5. Привязываем vk_user_id к пользователю
    user.vk_user_id = vk_user_id
    db.add(user)
    
    # 6. Создаем/обновляем VkBotAccount для отправки уведомлений ВК
    employee = None
    if user.iiko_id:
        employee = db.exec(select(Employee).where(Employee.iiko_id == user.iiko_id)).first()
        
    vk_account = None
    if employee:
        vk_account = db.exec(select(VkBotAccount).where(VkBotAccount.employee_id == employee.id)).first()
    if not vk_account:
        vk_account = db.exec(select(VkBotAccount).where(VkBotAccount.vk_user_id == vk_user_id)).first()
        
    if vk_account:
        vk_account.vk_user_id = vk_user_id
        vk_account.is_active = True
        vk_account.is_verified = True
        vk_account.use_vk = True
        if employee:
            vk_account.employee_id = employee.id
            if not vk_account.phone and employee.phone:
                vk_account.phone = employee.phone
    else:
        vk_account = VkBotAccount(
            vk_user_id=vk_user_id,
            name=employee.name if employee else (user.full_name or user.username),
            phone=employee.phone if employee else None,
            employee_id=employee.id if employee else None,
            is_active=True,
            is_verified=True,
            use_vk=True
        )
    db.add(vk_account)
    db.commit()
    db.refresh(vk_account)
    
    # Подписываем на события по умолчанию
    is_courier = (employee and employee.is_courier) or (user.role and user.role.code and user.role.code.upper() == "COURIER")
    default_events = ["change_cooking_time", "order_assigned", "order_changed"] if is_courier else ["order_new", "shift_close", "purchase_list_new"]
    
    for event in default_events:
        existing_sub = db.exec(select(VkBotSubscription).where(VkBotSubscription.account_id == vk_account.id, VkBotSubscription.event_type == event)).first()
        if not existing_sub:
            new_sub = VkBotSubscription(
                account_id=vk_account.id,
                event_type=event,
                delivery_mode=DeliveryMode.REALTIME,
                send_vk=True
            )
            db.add(new_sub)
    
    # 7. Генерируем JWT токен
    access_token_expires = timedelta(days=30)
    token = security.create_access_token(user.id, expires_delta=access_token_expires)
    
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "is_courier": is_courier,
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name
    }


