"""
API роутер полной интеграции с мессенджером MAX
Включает:
- Управление ботами (Bot API, platform-api2.max.ru, GET /me, Webhooks, Commands)
- Web Instance Bridge (QR авторизация, статус сессии, отключение)
- Поиск клиентов по номеру телефона (одиночный и пакетный)
- Универсальную отправку сообщений и уведомлений
- Журналы сообщений и вебхуков
- Прием входящих Webhook событий (старт бота, ответ на кнопку, передача контакта)
"""
import logging
import asyncio
import json
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select, desc
from app.core.database import get_session
from app.api.deps import require_permission
from app.models.user import User
from app.models.customer import Customer
from app.models.chat import MultichatAccount, MultichatMessage
from app.models.max_settings import MaxSettings, MaxBot, MaxMessageLog, MaxWebhookEvent
from app.services.max_service import (
    verify_bot_token,
    set_bot_webhook,
    delete_bot_webhook,
    get_bot_subscriptions,
    set_bot_commands,
    send_max_bot_message,
    send_max_message,
    DEFAULT_MAX_BASE_URL
)
from app.services.max_bridge_service import max_bridge_service

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Pydantic Схемы ---

class MaxBotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    bot_type: str = "MAX"
    bot_name: str
    bot_token: str
    bot_external_id: Optional[str] = None
    bot_username: Optional[str] = None
    bot_avatar: Optional[str] = None
    is_default_for_notifications: bool = False
    webhook_url: Optional[str] = None
    webhook_set: bool = False
    webhook_updated_at: Optional[datetime] = None
    commands_json: Optional[str] = None
    welcome_message: Optional[str] = "Здравствуйте! Я официальный бот для уведомлений о ваших заказах."
    request_contact_on_start: bool = True
    is_active: bool = True
    created_at: Optional[datetime] = None


class MaxSettingsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: str = DEFAULT_MAX_BASE_URL
    sender_name: Optional[str] = None
    default_template: Optional[str] = None
    is_active: bool = False
    send_priority: str = "bot_first"
    auto_search_phone: bool = True
    bots: List[MaxBotSchema] = []
    bridge_account: Optional[Dict[str, Any]] = None


def _bot_to_schema(b: MaxBot) -> MaxBotSchema:
    """Безопасное приведение модели MaxBot к схеме MaxBotSchema"""
    return MaxBotSchema(
        id=b.id,
        bot_type=b.bot_type or "MAX",
        bot_name=b.bot_name,
        bot_token=b.bot_token,
        bot_external_id=b.bot_external_id,
        bot_username=b.bot_username,
        bot_avatar=b.bot_avatar,
        is_default_for_notifications=bool(b.is_default_for_notifications),
        webhook_url=b.webhook_url,
        webhook_set=bool(b.webhook_set),
        webhook_updated_at=b.webhook_updated_at,
        commands_json=b.commands_json,
        welcome_message=b.welcome_message,
        request_contact_on_start=bool(b.request_contact_on_start),
        is_active=bool(b.is_active),
        created_at=b.created_at
    )


class VerifyBotRequest(BaseModel):
    token: str


class SetWebhookRequest(BaseModel):
    webhook_url: str


class SetCommandsRequest(BaseModel):
    commands: List[Dict[str, str]]


class TestSendMessageRequest(BaseModel):
    recipient: str
    text: str
    format: str = "markdown"
    notify: bool = True
    channel: Optional[str] = None  # "bot", "bridge" или auto
    buttons: Optional[List[List[Dict[str, Any]]]] = None


class PhoneSearchRequest(BaseModel):
    phone: str
    link_to_customer: bool = True


class BatchSearchRequest(BaseModel):
    limit: int = 20


# --- Вспомогательные функции ---

def _get_active_bridge_account(db: Session) -> Optional[Dict[str, Any]]:
    """Получение данных активного аккаунта Web Bridge"""
    acc = db.exec(
        select(MultichatAccount)
        .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
        .where(MultichatAccount.status == "active")
    ).first()
    if not acc:
        return None
    phone_val = acc.phone
    if not phone_val and acc.session_string:
        try:
            s_data = json.loads(acc.session_string)
            phone_val = s_data.get("phone")
        except Exception:
            pass
    return {
        "id": acc.id,
        "name": acc.name or "Личный аккаунт MAX",
        "phone": phone_val,
        "status": acc.status,
        "paired_at": acc.created_at.isoformat() if acc.created_at else None
    }


# ==========================================
# 1. ОБЩИЕ НАСТРОЙКИ MAX
# ==========================================

@router.get("/settings", response_model=MaxSettingsSchema)
def get_max_settings(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """Получение настроек MAX, списка ботов и статуса Web Bridge"""
    settings = db.exec(select(MaxSettings)).first()
    bridge_data = _get_active_bridge_account(db)
    
    if not settings:
        return MaxSettingsSchema(bridge_account=bridge_data)
    
    # Подготавливаем ответ
    res = MaxSettingsSchema(
        id=settings.id,
        api_key=settings.api_key,
        api_secret=settings.api_secret,
        base_url=settings.base_url or DEFAULT_MAX_BASE_URL,
        sender_name=settings.sender_name,
        default_template=settings.default_template,
        is_active=settings.is_active,
        send_priority=settings.send_priority or "bot_first",
        auto_search_phone=settings.auto_search_phone,
        bots=[_bot_to_schema(b) for b in (settings.bots or [])],
        bridge_account=bridge_data
    )
    return res


@router.post("/settings", response_model=MaxSettingsSchema)
def save_max_settings(
    data: MaxSettingsSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Сохранение основных настроек интеграции MAX"""
    settings = db.exec(select(MaxSettings)).first()
    
    if settings:
        settings.api_key = data.api_key
        settings.api_secret = data.api_secret
        settings.base_url = data.base_url
        settings.sender_name = data.sender_name
        settings.default_template = data.default_template
        settings.is_active = data.is_active
        settings.send_priority = data.send_priority
        settings.auto_search_phone = data.auto_search_phone
        settings.updated_at = datetime.now(timezone.utc)
    else:
        settings = MaxSettings(
            api_key=data.api_key,
            api_secret=data.api_secret,
            base_url=data.base_url,
            sender_name=data.sender_name,
            default_template=data.default_template,
            is_active=data.is_active,
            send_priority=data.send_priority,
            auto_search_phone=data.auto_search_phone
        )
        db.add(settings)
        
    db.commit()
    db.refresh(settings)
    
    bridge_data = _get_active_bridge_account(db)
    return MaxSettingsSchema(
        id=settings.id,
        api_key=settings.api_key,
        api_secret=settings.api_secret,
        base_url=settings.base_url,
        sender_name=settings.sender_name,
        default_template=settings.default_template,
        is_active=settings.is_active,
        send_priority=settings.send_priority,
        auto_search_phone=settings.auto_search_phone,
        bots=[_bot_to_schema(b) for b in (settings.bots or [])],
        bridge_account=bridge_data
    )


# ==========================================
# 2. УПРАВЛЕНИЕ БОТАМИ (Bot API)
# ==========================================

@router.get("/bots", response_model=List[MaxBotSchema])
def get_max_bots(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """Получение списка зарегистрированных ботов MAX"""
    settings = db.exec(select(MaxSettings)).first()
    if not settings or not settings.bots:
        return []
    return [_bot_to_schema(b) for b in settings.bots]


@router.post("/bots", response_model=MaxBotSchema)
async def add_max_bot(
    data: MaxBotSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Добавление нового бота MAX с автоматической верификацией токена"""
    settings = db.exec(select(MaxSettings)).first()
    if not settings:
        settings = MaxSettings(is_active=True, base_url=DEFAULT_MAX_BASE_URL)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    # Верифицируем токен через официальный API /me
    base_url = (settings.base_url or DEFAULT_MAX_BASE_URL).rstrip('/')
    verify_res = await verify_bot_token(data.bot_token, base_url=base_url)
    
    bot_ext_id = data.bot_external_id
    bot_username = data.bot_username
    bot_avatar = data.bot_avatar
    
    if verify_res.get("valid"):
        bot_ext_id = bot_ext_id or verify_res.get("bot_id")
        bot_username = bot_username or verify_res.get("bot_username")
        bot_avatar = bot_avatar or verify_res.get("bot_avatar")

    # Если бот помечен как default_for_notifications, снимаем признак с других
    if data.is_default_for_notifications:
        existing_defaults = db.exec(select(MaxBot).where(MaxBot.is_default_for_notifications == True)).all()
        for eb in existing_defaults:
            eb.is_default_for_notifications = False
            db.add(eb)

    new_bot = MaxBot(
        max_settings_id=settings.id,
        bot_type=data.bot_type or "MAX",
        bot_name=data.bot_name,
        bot_token=data.bot_token.strip(),
        bot_external_id=bot_ext_id,
        bot_username=bot_username,
        bot_avatar=bot_avatar,
        is_default_for_notifications=data.is_default_for_notifications,
        webhook_url=data.webhook_url,
        commands_json=data.commands_json,
        welcome_message=data.welcome_message,
        request_contact_on_start=data.request_contact_on_start,
        is_active=data.is_active
    )
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    return _bot_to_schema(new_bot)


@router.put("/bots/{bot_id}", response_model=MaxBotSchema)
def update_max_bot(
    bot_id: int,
    data: MaxBotSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Обновление параметров бота"""
    bot = db.get(MaxBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    # Если устанавливаем default_for_notifications, снимаем с остальных
    if data.is_default_for_notifications and not bot.is_default_for_notifications:
        existing_defaults = db.exec(select(MaxBot).where(MaxBot.id != bot_id).where(MaxBot.is_default_for_notifications == True)).all()
        for eb in existing_defaults:
            eb.is_default_for_notifications = False
            db.add(eb)

    bot.bot_name = data.bot_name
    bot.bot_token = data.bot_token.strip()
    bot.bot_type = data.bot_type
    bot.bot_external_id = data.bot_external_id
    bot.bot_username = data.bot_username
    bot.bot_avatar = data.bot_avatar
    bot.is_default_for_notifications = data.is_default_for_notifications
    bot.webhook_url = data.webhook_url
    bot.commands_json = data.commands_json
    bot.welcome_message = data.welcome_message
    bot.request_contact_on_start = data.request_contact_on_start
    bot.is_active = data.is_active
    bot.updated_at = datetime.now(timezone.utc)

    db.add(bot)
    db.commit()
    db.refresh(bot)
    return _bot_to_schema(bot)


@router.delete("/bots/{bot_id}")
async def delete_max_bot(
    bot_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Удаление бота с предварительным снятием вебхука"""
    bot = db.get(MaxBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    # Отписываемся от вебхука если он был зарегистрирован
    try:
        settings = db.exec(select(MaxSettings)).first()
        base_url = (settings.base_url if settings else DEFAULT_MAX_BASE_URL) or DEFAULT_MAX_BASE_URL
        await delete_bot_webhook(bot.bot_token, bot.webhook_url, base_url=base_url)
    except Exception as e:
        logger.warning(f"Ошибка отписки вебхука при удалении бота: {e}")

    db.delete(bot)
    db.commit()
    return {"status": "success", "message": "Бот успешно удален"}


@router.post("/bots/verify-token")
async def verify_new_bot_token(
    data: VerifyBotRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """Проверка токена бота MAX перед сохранением (GET /me)"""
    settings = db.exec(select(MaxSettings)).first()
    base_url = (settings.base_url if settings else DEFAULT_MAX_BASE_URL) or DEFAULT_MAX_BASE_URL
    res = await verify_bot_token(data.token, base_url=base_url)
    return res


@router.post("/bots/{bot_id}/verify")
async def verify_bot_connection(
    bot_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """Проверка подключения бота к серверам MAX (GET /me)"""
    bot = db.get(MaxBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    settings = db.exec(select(MaxSettings)).first()
    base_url = (settings.base_url if settings else DEFAULT_MAX_BASE_URL) or DEFAULT_MAX_BASE_URL
    res = await verify_bot_token(bot.bot_token, base_url=base_url)

    if res.get("valid"):
        # Обновляем имя, юзернейм и аватарку бота
        if res.get("bot_id"):
            bot.bot_external_id = res.get("bot_id")
        if res.get("bot_username"):
            bot.bot_username = res.get("bot_username")
        if res.get("bot_avatar"):
            bot.bot_avatar = res.get("bot_avatar")
        db.add(bot)
        db.commit()
        db.refresh(bot)
        return {
            "status": "success",
            "message": f"Бот успешно проверен: @{bot.bot_username or bot.bot_name} (ID: {bot.bot_external_id})",
            "bot": res
        }
    else:
        return {
            "status": "error",
            "message": res.get("error", "Не удалось подтвердить токен бота")
        }


@router.post("/bots/{bot_id}/webhook/set")
async def set_webhook(
    bot_id: int,
    data: SetWebhookRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Регистрация Webhook URL в MAX для получения входящих событий"""
    bot = db.get(MaxBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    settings = db.exec(select(MaxSettings)).first()
    base_url = (settings.base_url if settings else DEFAULT_MAX_BASE_URL) or DEFAULT_MAX_BASE_URL
    
    res = await set_bot_webhook(bot.bot_token, data.webhook_url, base_url=base_url)
    if res.get("success"):
        bot.webhook_url = data.webhook_url
        bot.webhook_set = True
        bot.webhook_updated_at = datetime.now(timezone.utc)
        db.add(bot)
        db.commit()
        return {"status": "success", "message": "Webhook успешно установлен в MAX"}
    else:
        raise HTTPException(status_code=400, detail=res.get("error", "Не удалось установить Webhook"))


@router.post("/bots/{bot_id}/webhook/delete")
async def delete_webhook(
    bot_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Удаление подписки Webhook в MAX"""
    bot = db.get(MaxBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    settings = db.exec(select(MaxSettings)).first()
    base_url = (settings.base_url if settings else DEFAULT_MAX_BASE_URL) or DEFAULT_MAX_BASE_URL

    res = await delete_bot_webhook(bot.bot_token, bot.webhook_url, base_url=base_url)
    bot.webhook_set = False
    bot.webhook_updated_at = datetime.now(timezone.utc)
    db.add(bot)
    db.commit()
    return {"status": "success", "message": "Webhook успешно удален из MAX"}


@router.post("/bots/{bot_id}/commands")
async def update_bot_commands(
    bot_id: int,
    data: SetCommandsRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Обновление списка команд бота в меню MAX (PATCH /me)"""
    bot = db.get(MaxBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    settings = db.exec(select(MaxSettings)).first()
    base_url = (settings.base_url if settings else DEFAULT_MAX_BASE_URL) or DEFAULT_MAX_BASE_URL

    res = await set_bot_commands(bot.bot_token, data.commands, base_url=base_url)
    if res.get("success"):
        bot.commands_json = json.dumps(data.commands, ensure_ascii=False)
        db.add(bot)
        db.commit()
        return {"status": "success", "message": "Команды бота успешно синхронизированы с MAX"}
    else:
        raise HTTPException(status_code=400, detail=res.get("error", "Ошибка обновления команд"))


# ==========================================
# 3. WEB INSTANCE BRIDGE (Личный аккаунт / QR)
# ==========================================

@router.post("/bridge/qr/init")
async def init_bridge_qr(
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Генерация сессии привязки и QR-кода от серверов MAX"""
    try:
        session_data = await max_bridge_service.init_qr_session()
        return session_data
    except Exception as e:
        logger.error(f"Ошибка инициализации QR-сессии MAX: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bridge/qr/status/{session_id}")
def check_bridge_qr_status(
    session_id: str,
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """Проверка статуса авторизации сессии по QR-коду"""
    return max_bridge_service.get_session_status(session_id)


@router.get("/bridge/account")
def get_bridge_account(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """Получение информации о текущем подключенном аккаунте MAX"""
    acc = _get_active_bridge_account(db)
    if not acc:
        return {"connected": False}
    return {"connected": True, "account": acc}


@router.post("/bridge/disconnect")
def disconnect_bridge(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Отключение активной сессии Web Bridge"""
    acc = db.exec(
        select(MultichatAccount)
        .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
        .where(MultichatAccount.status == "active")
    ).first()
    if not acc:
        return {"status": "success", "message": "Нет активных подключений"}

    max_bridge_service.disconnect_session(acc.id)
    return {"status": "success", "message": "Аккаунт MAX успешно отключен"}


# ==========================================
# 4. ПОИСК КЛИЕНТОВ ПО НОМЕРУ ТЕЛЕФОНА
# ==========================================

@router.post("/search-phone")
async def search_client_by_phone(
    data: PhoneSearchRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """
    Поиск пользователя MAX в реальном времени по номеру телефона
    и опциональная привязка найденного ID к карточке Customer.
    """
    res = await max_bridge_service.search_user_by_phone(data.phone, db)
    return res


@router.post("/batch-search-phones")
async def batch_search_phones(
    data: BatchSearchRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """Пакетный поиск MAX ID для клиентов CRM без привязки"""
    res = await max_bridge_service.batch_search_customers(db, limit=data.limit)
    return res


# ==========================================
# 5. ОТПРАВКА СООБЩЕНИЙ И ТЕСТОВ
# ==========================================

@router.post("/send-message")
async def send_message_api(
    data: TestSendMessageRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_edit"))
):
    """
    Универсальная отправка сообщения через интеллектуальный маршрутизатор:
    Bot API (user_id/chat_id) или Web Instance Bridge (номер телефона).
    """
    res = await send_max_message(
        recipient=data.recipient,
        text=data.text,
        session=db,
        format=data.format,
        notify=data.notify,
        buttons=data.buttons,
        prefer_channel=data.channel
    )
    if res.get("success"):
        return {"status": "success", "data": res}
    else:
        raise HTTPException(status_code=400, detail=res.get("error", "Не удалось доставить сообщение в MAX"))


# ==========================================
# 6. ЖУРНАЛ СООБЩЕНИЙ И ВЕБХУКОВ
# ==========================================

@router.get("/logs")
def get_message_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    channel: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """Получение журнала отправленных сообщений MAX"""
    query = select(MaxMessageLog).order_by(desc(MaxMessageLog.created_at))
    if status:
        query = query.where(MaxMessageLog.status == status)
    if channel:
        query = query.where(MaxMessageLog.channel_type == channel)

    total_count = len(db.exec(query).all())
    items = db.exec(query.offset(offset).limit(limit)).all()
    return {"total": total_count, "items": items}


@router.get("/webhook/events")
def get_webhook_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_max_view"))
):
    """Получение истории входящих вебхук-событий MAX"""
    query = select(MaxWebhookEvent).order_by(desc(MaxWebhookEvent.created_at))
    total_count = len(db.exec(query).all())
    items = db.exec(query.offset(offset).limit(limit)).all()
    return {"total": total_count, "items": items}


# ==========================================
# 7. ПРИЕМ ВХОДЯЩИХ WEBHOOK СОБЫТИЙ (Публичные)
# ==========================================

@router.post("/webhook")
@router.post("/webhook/{bot_id}")
async def receive_max_webhook(
    request: Request,
    bot_id: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """
    Публичный обработчик входящих Webhook от мессенджера MAX:
    - bot_started: пользователь нажал кнопку Старт в боте
    - message_created: входящее текстовое сообщение
    - message_callback: нажатие инлайн-кнопки
    - contact_received / vcf_info: передача контакта (связка Customer с max_user_id)
    """
    try:
        body_bytes = await request.body()
        if not body_bytes:
            return {"ok": True}
        data = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        logger.warning(f"Ошибка парсинга webhook MAX: {e}")
        return {"ok": False, "error": "Invalid JSON"}

    event_type = data.get("update_type") or data.get("event") or data.get("type") or "unknown"
    user_id = None
    chat_id = None

    # Извлекаем user_id / chat_id из структуры
    sender = data.get("sender") or {}
    if isinstance(sender, dict):
        user_id = str(sender.get("user_id") or sender.get("id") or "")
    
    msg_obj = data.get("message") or {}
    if isinstance(msg_obj, dict):
        if not user_id:
            sender_m = msg_obj.get("sender") or {}
            user_id = str(sender_m.get("user_id") or sender_m.get("id") or "")
        chat_id = str(msg_obj.get("chat_id") or msg_obj.get("recipient", {}).get("chat_id") or "")

    # Обработка нажатия инлайн-кнопок курьером (message_callback)
    callback_payload = None
    if event_type in ["message_callback", "callback"] or data.get("callback"):
        cb_obj = data.get("callback") or {}
        callback_payload = cb_obj.get("payload") or data.get("payload")
    if not callback_payload and isinstance(data.get("payload"), str):
        callback_payload = data.get("payload")

    if callback_payload and str(callback_payload).startswith("cdeliv:"):
        parts = str(callback_payload).split(":")
        if len(parts) >= 3:
            try:
                order_id = int(parts[1])
                pay = parts[2]
                from app.services.vk_notification_router import handle_courier_order_action
                asyncio.create_task(handle_courier_order_action(order_id, pay, "max", str(user_id or "")))
            except Exception as e_mcb:
                logger.error(f"Error handling MAX courier delivery callback: {e_mcb}")
        return {"ok": True}

    # Логируем событие в max_webhook_events
    try:
        wb_event = MaxWebhookEvent(
            bot_id=bot_id,
            event_type=event_type,
            user_id=user_id,
            chat_id=chat_id,
            payload_json=json.dumps(data, ensure_ascii=False)
        )
        db.add(wb_event)
        db.commit()
    except Exception as log_ex:
        logger.error(f"Не удалось записать входящий вебхук MAX в БД: {log_ex}")

    # Обработка передачи контакта (contact_received)
    contact = data.get("contact") or msg_obj.get("contact")
    if contact and user_id:
        raw_phone = contact.get("phone_number") or contact.get("phone") or ""
        clean_p = "".join(filter(str.isdigit, str(raw_phone)))
        if len(clean_p) >= 10:
            cust = db.exec(select(Customer).where(Customer.phone.like(f"%{clean_p[-10:]}%"))).first()
            if cust:
                cust.max_user_id = user_id
                db.add(cust)
                db.commit()
                logger.info(f"Связан клиент ID={cust.id} с MAX user_id={user_id} через контакт Webhook")

    # Обработка bot_started (отправка приветствия и кнопки запроса контакта)
    if event_type in ["bot_started", "user_started"] and bot_id:
        bot = db.get(MaxBot, bot_id)
        if bot and bot.is_active and user_id:
            settings = db.exec(select(MaxSettings)).first()
            base_url = (settings.base_url if settings else DEFAULT_MAX_BASE_URL) or DEFAULT_MAX_BASE_URL
            
            buttons = None
            if bot.request_contact_on_start:
                buttons = [[{"type": "request_contact", "text": "📱 Поделиться номером для скидок и бонусов"}]]

            welcome = bot.welcome_message or "Здравствуйте! Я официальный бот для уведомлений о ваших заказах."
            asyncio.create_task(send_max_bot_message(
                token=bot.bot_token,
                recipient=user_id,
                text=welcome,
                format="markdown",
                buttons=buttons,
                base_url=base_url
            ))

    # Обработка входящего сообщения бота для Мультичата (message_created, new_message)
    msg_text = (
        msg_obj.get("text") or 
        (msg_obj.get("body", {}).get("text") if isinstance(msg_obj.get("body"), dict) else "") or
        data.get("text") or
        ""
    )
    
    clean_txt = (msg_text or "").strip().lower()
    if clean_txt.startswith("д ") or clean_txt.startswith("доставлен "):
        words = clean_txt.split()
        if len(words) >= 2:
            num_part = words[1].replace("#", "")
            pay_part = "paid"
            if len(words) >= 3:
                p_word = words[2]
                if "сбп" in p_word or "qr" in p_word:
                    pay_part = "sbp"
                elif "нал" in p_word:
                    pay_part = "cash"
                elif "карт" in p_word or "терм" in p_word:
                    pay_part = "card"
            try:
                from app.models.order import Order
                from app.services.vk_notification_router import handle_courier_order_action
                q = select(Order).where((Order.external_number == num_part) | (Order.iiko_order_number == num_part))
                if num_part.isdigit():
                    q = select(Order).where((Order.external_number == num_part) | (Order.iiko_order_number == num_part) | (Order.id == int(num_part)))
                found_ord = db.exec(q).first()
                if found_ord:
                    asyncio.create_task(handle_courier_order_action(found_ord.id, pay_part, "max", str(user_id or "")))
            except Exception as e_cmd:
                logger.error(f"Error in MAX courier text command: {e_cmd}")

    has_media = bool(msg_obj.get("attachments") or msg_obj.get("payload"))
    if (event_type in ["message_created", "new_message", "message"] or msg_text) and user_id and (msg_text or has_media):
        sender_obj = msg_obj.get("sender") or data.get("sender") or {}
        first_name = sender_obj.get("first_name") or ""
        last_name = sender_obj.get("last_name") or ""
        full_n = f"{first_name} {last_name}".strip()
        sender_name = full_n or sender_obj.get("name") or sender_obj.get("username") or f"Пользователь MAX {user_id}"
        avatar_url = sender_obj.get("avatar_url") or sender_obj.get("photo_url") or None
        
        # Проверяем, является ли отправитель ботом
        bot_instance = db.get(MaxBot, bot_id) if bot_id else None
        is_bot_sender = bool(sender_obj.get("is_bot") or (bot_instance and str(bot_instance.bot_id) == str(user_id)))
        direction = "outbound" if is_bot_sender else "inbound"
        target_peer_id = user_id if not is_bot_sender else str(msg_obj.get("recipient", {}).get("chat_id") or chat_id or user_id)

        # Проверяем привязанного клиента
        cust = db.exec(select(Customer).where(Customer.max_user_id == target_peer_id)).first()
        if cust:
            c_name = f"{cust.first_name or cust.name or ''} {cust.last_name or cust.surname or ''}".strip()
            if c_name:
                sender_name = c_name

        channel_id_str = str(bot_id) if bot_id else None
        ext_msg_id = str(msg_obj.get("mid") or msg_obj.get("id") or f"max_bot_{user_id}_{int(datetime.now(timezone.utc).timestamp())}")

        chat_msg = MultichatMessage(
            channel="max_bot",
            channel_id=channel_id_str,
            peer_id=target_peer_id,
            peer_name=sender_name,
            peer_avatar=avatar_url,
            from_id=user_id,
            text=msg_text or "[Вложение / Медиа]",
            direction=direction,
            external_id=ext_msg_id,
            created_at=datetime.now(timezone.utc),
            is_read=is_bot_sender,
            payload=data
        )
        db.add(chat_msg)
        db.commit()
        db.refresh(chat_msg)
        logger.info(f"Входящее сообщение MAX Bot сохранено: от {sender_name} ({user_id}): {msg_text[:30]}")

        try:
            from app.api.multichat import broadcast_ws_message
            asyncio.create_task(broadcast_ws_message(chat_msg))
        except Exception as ws_err:
            logger.debug(f"WS broadcast error for MAX bot message: {ws_err}")

    return {"ok": True}
