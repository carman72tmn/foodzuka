from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select
from app.core.database import get_session
from app.api.deps import require_permission
from app.models.user import User
from app.models.vk_settings import VkSettings
from app.models.vk_webhook_log import VkWebhookLog
from app.models.vk_message import VkMessage
from app.models.vk_user import VkUser
from app.models.vk_bot_connection import VkBotConnection
from app.core.datetime_utils import utc_now
from app.services.vk_service import process_vk_event
from pydantic import BaseModel
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter()

class VkBotConnectionSchema(BaseModel):
    id: int | None = None
    name: str
    vk_bot_token: str
    vk_user_token: str | None = None
    vk_group_id: int
    vk_confirmation_code: str | None = None
    vk_secret_key: str | None = None
    is_active: bool = True
    is_main: bool = False
    use_longpoll: bool = False
    created_at: Any | None = None
    updated_at: Any | None = None

class VkBotStatsResponse(BaseModel):
    id: int
    name: str
    vk_group_id: int
    is_active: bool
    is_main: bool
    use_longpoll: bool = False
    linked_users_count: int
    total_events_count: int
    events_by_type: Dict[str, int]
    scan_status: Dict[str, Any] | None = None
    last_scan_at: Any | None = None
    vk_bot_token: str | None = None
    vk_user_token: str | None = None
    vk_secret_key: str | None = None
    vk_confirmation_code: str | None = None


class VkSettingsSchema(BaseModel):
    vk_bot_token: str | None = None
    vk_confirmation_code: str | None = None
    vk_group_id: str | None = None
    vk_secret_key: str | None = None
    vk_parser_enabled: bool = False
    vk_parser_phrase: str | None = None
    vk_parser_mask: str | None = None
    vk_parser_ignored_ids: str | None = None
    vk_parser_last_scan_at: Any | None = None
    vk_parser_scan_status: Dict[str, Any] | None = None
    vk_notification_settings: Dict[str, Any] | None = None
    vk_app_id: str | None = None
    vk_app_secret: str | None = None

class VkMessageResponse(BaseModel):
    id: int
    vk_message_id: int
    peer_id: int
    from_id: int
    text: str
    direction: str
    created_at: Any
    user: Dict[str, Any] | None = None

class VkMessageStatsResponse(BaseModel):
    total: int
    inbound: int
    outbound: int

@router.post("/parser/scan")
def start_historical_scan(db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_parser_edit"))):
    """Запуск ретроспективного сканирования истории сообщений"""
    from app.tasks.vk_parser_tasks import scan_vk_history_task
    
    # Проверяем, не запущено ли уже сканирование
    vk_settings = db.exec(select(VkSettings)).first()
    if vk_settings and vk_settings.vk_parser_scan_status:
        if vk_settings.vk_parser_scan_status.get("status") == "running":
            return {"status": "error", "message": "Сканирование уже запущено"}
            
    scan_vk_history_task.delay()
    return {"status": "success", "message": "Задача сканирования добавлена в очередь"}

@router.get("/parser/scan/status")
def get_scan_status(db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_parser_view"))):
    """Получение текущего статуса сканирования"""
    vk_settings = db.exec(select(VkSettings)).first()
    if not vk_settings:
        return {"status": "idle"}
    return vk_settings.vk_parser_scan_status or {"status": "idle"}

@router.get("/parser/stats")
def get_parser_stats(db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_parser_view"))):
    """Получение статистики парсинга VK"""
    from app.models.vk_user import VkUser
    from sqlalchemy import func
    
    total_linked = db.exec(select(func.count(VkUser.vk_id)).where(VkUser.is_linked == True)).one()
    linked_realtime = db.exec(select(func.count(VkUser.vk_id)).where(VkUser.linking_source == "parser_realtime")).one()
    linked_history = db.exec(select(func.count(VkUser.vk_id)).where(VkUser.linking_source == "parser_history")).one()
    
    recent_links = db.exec(
        select(VkUser)
        .where(VkUser.is_linked == True)
        .order_by(VkUser.linked_at.desc())
        .limit(20)
    ).all()
    
    return {
        "summary": {
            "total_linked": total_linked,
            "linked_realtime": linked_realtime,
            "linked_history": linked_history
        },
        "recent_links": recent_links
    }

@router.get("/parser/messages/stats", response_model=VkMessageStatsResponse)
def get_message_stats(date: str | None = None, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_parser_view"))):
    """Получение статистики сообщений"""
    from sqlalchemy import func, cast, Date
    
    query_total = select(func.count(VkMessage.id))
    query_inbound = select(func.count(VkMessage.id)).where(VkMessage.direction == "inbound")
    query_outbound = select(func.count(VkMessage.id)).where(VkMessage.direction == "outbound")
    
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            query_total = query_total.where(cast(VkMessage.created_at, Date) == filter_date)
            query_inbound = query_inbound.where(cast(VkMessage.created_at, Date) == filter_date)
            query_outbound = query_outbound.where(cast(VkMessage.created_at, Date) == filter_date)
        except ValueError:
            pass
            
    total = db.exec(query_total).one()
    inbound = db.exec(query_inbound).one()
    outbound = db.exec(query_outbound).one()
    
    return {
        "total": total,
        "inbound": inbound,
        "outbound": outbound
    }

@router.get("/parser/messages")
def get_messages(
    page: int = 1, 
    per_page: int = 50, 
    direction: str | None = None,
    search: str | None = None,
    date: str | None = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_vk_parser_view"))
):
    """Получение списка сообщений с пагинацией, поиском и фильтром по дате"""
    from sqlalchemy import or_, desc, cast, Date, func
    
    query = select(VkMessage, VkUser).join(VkUser, VkMessage.peer_id == VkUser.vk_id, isouter=True)
    count_query = select(func.count(VkMessage.id))
    
    if direction:
        query = query.where(VkMessage.direction == direction)
        count_query = count_query.where(VkMessage.direction == direction)
    
    if search:
        query = query.where(VkMessage.text.ilike(f"%{search}%"))
        count_query = count_query.where(VkMessage.text.ilike(f"%{search}%"))
        
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.where(cast(VkMessage.created_at, Date) == filter_date)
            count_query = count_query.where(cast(VkMessage.created_at, Date) == filter_date)
        except ValueError:
            pass
    
    total_count = db.exec(count_query).one()
    
    # Получаем данные
    results = db.exec(
        query.order_by(desc(VkMessage.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()
    
    messages = []
    for msg, user in results:
        msg_dict = msg.model_dump()
        if user:
            msg_dict["user"] = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "photo_50": user.photo_50,
                "screen_name": user.screen_name
            }
        else:
            msg_dict["user"] = None
        messages.append(msg_dict)
    
    return {
        "items": messages,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page
    }

class VkLogResponse(BaseModel):
    id: int
    event_type: str
    payload: Dict[str, Any]
    created_at: Any

@router.get("/settings", response_model=VkSettingsSchema)
def get_vk_settings(db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_parser_view"))):
    result = db.execute(select(VkSettings))
    settings_db = result.scalars().first()
    if not settings_db:
        return VkSettingsSchema()
    return settings_db

@router.post("/settings", response_model=VkSettingsSchema)
def save_vk_settings(data: VkSettingsSchema, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_parser_edit"))):
    result = db.execute(select(VkSettings))
    settings_db = result.scalars().first()
    
    if settings_db:
        if data.vk_bot_token is not None:
            settings_db.vk_bot_token = data.vk_bot_token
        if data.vk_confirmation_code is not None:
            settings_db.vk_confirmation_code = data.vk_confirmation_code
        if data.vk_group_id is not None:
            settings_db.vk_group_id = data.vk_group_id
        if data.vk_secret_key is not None:
            settings_db.vk_secret_key = data.vk_secret_key
            
        settings_db.vk_parser_enabled = data.vk_parser_enabled
        settings_db.vk_parser_phrase = data.vk_parser_phrase
        settings_db.vk_parser_mask = data.vk_parser_mask
        settings_db.vk_parser_ignored_ids = data.vk_parser_ignored_ids
        settings_db.vk_notification_settings = data.vk_notification_settings
        if data.vk_app_id is not None:
            settings_db.vk_app_id = data.vk_app_id
        if data.vk_app_secret is not None:
            settings_db.vk_app_secret = data.vk_app_secret
    else:
        settings_db = VkSettings(**data.model_dump())
        db.add(settings_db)
        
    db.commit()
    db.refresh(settings_db)
    return settings_db

def migrate_settings_to_connections_logic(db: Session):
    existing_bots = db.exec(select(VkBotConnection)).all()
    if not existing_bots:
        vk_settings = db.exec(select(VkSettings)).first()
        if vk_settings and vk_settings.vk_bot_token and vk_settings.vk_group_id:
            main_bot = VkBotConnection(
                name="Основной бот",
                vk_bot_token=vk_settings.vk_bot_token,
                vk_group_id=int(vk_settings.vk_group_id),
                vk_confirmation_code=vk_settings.vk_confirmation_code,
                vk_secret_key=vk_settings.vk_secret_key,
                is_active=True,
                is_main=True
            )
            db.add(main_bot)
            db.commit()

@router.get("/bots", response_model=List[VkBotStatsResponse])
def get_vk_bots(db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_view"))):
    """Получение списка всех ботов с их статистикой"""
    migrate_settings_to_connections_logic(db)
    
    bots = db.exec(select(VkBotConnection)).all()
    result = []
    for bot in bots:
        # 1. Считаем связанных пользователей для этой группы
        from sqlalchemy import func
        linked_users_count = db.exec(
            select(func.count(VkUser.vk_id))
            .where(VkUser.vk_group_id == bot.vk_group_id)
            .where(VkUser.is_linked == True)
        ).one() or 0
        
        # 2. Считаем события Callback API для этой группы
        total_events_count = db.exec(
            select(func.count(VkWebhookLog.id))
            .where(VkWebhookLog.vk_group_id == bot.vk_group_id)
        ).one() or 0
        
        # 3. Группируем по типам событий
        events_by_type = {}
        events_grouped = db.exec(
            select(VkWebhookLog.event_type, func.count(VkWebhookLog.id))
            .where(VkWebhookLog.vk_group_id == bot.vk_group_id)
            .group_by(VkWebhookLog.event_type)
        ).all()
        for evt_type, count in events_grouped:
            events_by_type[evt_type] = count
            
        result.append({
            "id": bot.id,
            "name": bot.name,
            "vk_group_id": bot.vk_group_id,
            "is_active": bot.is_active,
            "is_main": bot.is_main,
            "linked_users_count": linked_users_count,
            "total_events_count": total_events_count,
            "events_by_type": events_by_type,
            "scan_status": bot.scan_status,
            "last_scan_at": bot.last_scan_at,
            "use_longpoll": bot.use_longpoll,
            "vk_bot_token": "********" if bot.vk_bot_token else "",
            "vk_user_token": "********" if bot.vk_user_token else "",
            "vk_secret_key": "********" if bot.vk_secret_key else "",
            "vk_confirmation_code": bot.vk_confirmation_code or ""
        })
    return result

@router.post("/bots", response_model=VkBotConnectionSchema)
def create_vk_bot(data: VkBotConnectionSchema, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_edit"))):
    """Добавление нового бота"""
    if data.is_main:
        db.execute(text("UPDATE vk_bot_connections SET is_main = FALSE"))
        db.commit()
        
    bot = VkBotConnection(
        name=data.name,
        vk_bot_token=data.vk_bot_token,
        vk_user_token=data.vk_user_token,
        vk_group_id=data.vk_group_id,
        vk_confirmation_code=data.vk_confirmation_code,
        vk_secret_key=data.vk_secret_key,
        is_active=data.is_active,
        is_main=data.is_main,
        use_longpoll=data.use_longpoll
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    
    # Запуск Long Poll если активен и выбран
    from app.services.vk_longpoll_service import vk_longpoll_manager
    if bot.is_active and bot.use_longpoll:
        vk_longpoll_manager.start_bot(bot.id)
        
    return bot

@router.patch("/bots/{bot_id}", response_model=VkBotConnectionSchema)
def update_vk_bot(bot_id: int, data: Dict[str, Any], db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_edit"))):
    """Обновление настроек бота"""
    bot = db.get(VkBotConnection, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
        
    if data.get("is_main"):
        db.execute(text("UPDATE vk_bot_connections SET is_main = FALSE WHERE id != :id"), {"id": bot_id})
        db.commit()
        
    for key, value in data.items():
        if key in ("vk_bot_token", "vk_user_token", "vk_secret_key") and value == "********":
            continue
        if hasattr(bot, key):
            setattr(bot, key, value)
            
    bot.updated_at = utc_now()
    db.add(bot)
    db.commit()
    db.refresh(bot)
    
    # Управляем Long Poll задачей в зависимости от новых настроек
    from app.services.vk_longpoll_service import vk_longpoll_manager
    if bot.is_active and bot.use_longpoll:
        vk_longpoll_manager.start_bot(bot.id)
    else:
        vk_longpoll_manager.stop_bot(bot.id)
        
    return bot

@router.delete("/bots/{bot_id}")
def delete_vk_bot(bot_id: int, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_edit"))):
    """Удаление бота"""
    bot = db.get(VkBotConnection, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
        
    # Останавливаем Long Poll задачу перед удалением
    from app.services.vk_longpoll_service import vk_longpoll_manager
    vk_longpoll_manager.stop_bot(bot_id)
    
    db.delete(bot)
    db.commit()
    return {"status": "success", "message": "Бот успешно удален"}

@router.post("/bots/{bot_id}/test-connection")
async def test_specific_vk_connection(bot_id: int, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_edit"))):
    """Проверка соединения с конкретным ботом"""
    bot = db.get(VkBotConnection, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.vk.ru/method/groups.getById",
                params={
                    "access_token": bot.vk_bot_token,
                    "v": "5.199"
                }
            )
            res_data = response.json()
            if "error" in res_data:
                return {"status": "error", "message": res_data["error"].get("error_msg", "Ошибка API VK")}
            return {"status": "success", "message": "Соединение с VK успешно установлено", "data": res_data.get("response")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

@router.post("/bots/{bot_id}/scan")
def start_bot_historical_scan(bot_id: int, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_edit"))):
    """Запуск сканирования истории для конкретного бота"""
    from app.tasks.vk_parser_tasks import scan_vk_history_task
    
    bot = db.get(VkBotConnection, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
        
    if bot.scan_status and bot.scan_status.get("status") == "running":
        return {"status": "error", "message": "Сканирование этого бота уже запущено"}
        
    scan_vk_history_task.delay(bot_id)
    return {"status": "success", "message": "Задача сканирования бота добавлена в очередь"}

@router.get("/bots/{bot_id}/scan/status")
def get_bot_scan_status(bot_id: int, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_view"))):
    """Получение статуса сканирования для конкретного бота"""
    bot = db.get(VkBotConnection, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
    return bot.scan_status or {"status": "idle"}

@router.get("/test-connection")
async def test_vk_connection(db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_edit"))):
    """Проверка валидности токена бота"""
    result = db.execute(select(VkSettings))
    vk_settings = result.scalars().first()
    
    if not vk_settings or not vk_settings.vk_bot_token:
        raise HTTPException(status_code=400, detail="Токен бота не настроен")
        
    async with httpx.AsyncClient() as client:
        try:
            # Простейший запрос к API VK для проверки токена
            response = await client.get(
                "https://api.vk.ru/method/groups.getById",
                params={
                    "access_token": vk_settings.vk_bot_token,
                    "v": "5.199"
                }
            )
            data = response.json()
            if "error" in data:
                return {"status": "error", "message": data["error"].get("error_msg", "Ошибка API VK")}
            return {"status": "success", "message": "Соединение с VK успешно установлено", "data": data.get("response")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

@router.post("/webhook")
async def vk_webhook(request: Request, db: Session = Depends(get_session)):
    try:
        data = await request.json()
    except Exception as e:
        print(f"VK Webhook JSON error: {e}")
        # Попробуем прочитать сырое тело для отладки
        body = await request.body()
        print(f"VK Webhook Raw Body: {body.decode(errors='ignore')}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        
    event_type = data.get("type")
    group_id = data.get("group_id")
    
    # Логируем входящее событие
    try:
        log_entry = VkWebhookLog(event_type=event_type or "unknown", payload=data, vk_group_id=group_id)
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Ошибка при сохранении лога VK: {e}")

    # Ищем бота по vk_group_id
    bot = None
    if group_id:
        bot = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)).first()

    # Фолбэк на глобальные настройки для обратной совместимости
    vk_settings = db.exec(select(VkSettings)).first()
    
    # Проверка секретного ключа
    secret_key = None
    if bot:
        secret_key = bot.vk_secret_key
    elif vk_settings and vk_settings.vk_group_id == group_id:
        secret_key = vk_settings.vk_secret_key
        
    if secret_key and data.get("secret") != secret_key:
        if event_type != "confirmation":
            raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # Confirmation event
    if event_type == "confirmation":
        if bot and bot.vk_confirmation_code:
            return PlainTextResponse(content=bot.vk_confirmation_code)
        if vk_settings and vk_settings.vk_group_id == group_id and vk_settings.vk_confirmation_code:
            return PlainTextResponse(content=vk_settings.vk_confirmation_code)
        return PlainTextResponse(content="ok")
    
    # Получаем токен
    bot_token = None
    if bot:
        bot_token = bot.vk_bot_token
    elif vk_settings and vk_settings.vk_group_id == group_id:
        bot_token = vk_settings.vk_bot_token
        
    try:
        await process_vk_event(data, db, bot_token, group_id)
    except Exception as e:
        logger.error(f"Error processing VK event: {e}")
        
    return PlainTextResponse(content="ok")

@router.get("/logs", response_model=List[VkLogResponse])
def get_vk_logs(vk_group_id: int | None = None, limit: int = 50, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_view"))):
    """Получение последних событий VK с возможностью фильтрации по группе"""
    query = select(VkWebhookLog)
    if vk_group_id is not None:
        query = query.where(VkWebhookLog.vk_group_id == vk_group_id)
    result = db.execute(
        query.order_by(VkWebhookLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()

@router.delete("/parser/users/{vk_id}/link")
def unlink_vk_user(vk_id: int, db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_parser_edit"))):
    """Удаление привязки пользователя VK к клиенту"""
    from app.models.customer import Customer
    
    # 1. Находим пользователя VK
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if not vk_user:
        raise HTTPException(status_code=404, detail="Пользователь VK не найден")
        
    # 2. Сбрасываем поля привязки в vk_users
    vk_user.is_linked = False
    vk_user.phone = None
    vk_user.iiko_customer_id = None
    vk_user.linking_source = None
    vk_user.last_order_id = None
    db.add(vk_user)
    
    # 3. Убираем привязку в таблице customers
    customers = db.exec(select(Customer).where(Customer.vk_user_id == vk_id)).all()
    for customer in customers:
        customer.vk_user_id = None
        db.add(customer)
        
    db.commit()
    return {"status": "success", "message": "Привязка удалена"}

@router.post("/parser/messages/cleanup")
def cleanup_old_messages(db: Session = Depends(get_session), current_user: User = Depends(require_permission("settings_vk_parser_edit"))):
    """Удаление сообщений старше 90 дней"""
    from datetime import timedelta
    from app.core.datetime_utils import utc_now
    from sqlalchemy import delete
    
    threshold = utc_now() - timedelta(days=90)
    
    # Используем delete statement для эффективности
    statement = delete(VkMessage).where(VkMessage.created_at < threshold)
    result = db.exec(statement)
    db.commit()
    
    deleted_count = result.rowcount
    logger.info(f"Cleanup: deleted {deleted_count} messages older than {threshold}")
    
    return {
        "status": "success", 
        "message": f"Удалено сообщений: {deleted_count}",
        "deleted_count": deleted_count
    }


class VkLinkedAccountUpdateSchema(BaseModel):
    is_blocked: bool | None = None
    notifications_enabled: bool | None = None


@router.get("/parser/linked-accounts")
def get_linked_accounts(
    page: int = 1,
    per_page: int = 50,
    search: str | None = None,
    filter_status: str = "all", # all, active, blocked
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_vk_parser_view"))
):
    """Получение списка связанных аккаунтов гостей в VK парсере"""
    from app.models.customer import Customer
    from sqlalchemy import or_, desc, func

    # Базовый запрос
    query = select(VkUser, Customer).join(Customer, VkUser.phone == Customer.phone, isouter=True).where(VkUser.is_linked == True)
    count_query = select(func.count(VkUser.vk_id)).where(VkUser.is_linked == True)

    # Поиск по имени, фамилии или телефону
    if search:
        search_filter = or_(
            VkUser.phone.ilike(f"%{search}%"),
            VkUser.first_name.ilike(f"%{search}%"),
            VkUser.last_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Фильтрация по статусу
    if filter_status == "blocked":
        query = query.where(VkUser.is_blocked == True)
        count_query = count_query.where(VkUser.is_blocked == True)
    elif filter_status == "active":
        query = query.where(VkUser.is_blocked == False)
        count_query = count_query.where(VkUser.is_blocked == False)

    total_count = db.exec(count_query).one()

    # Сортировка по дате привязки
    results = db.exec(
        query.order_by(desc(VkUser.linked_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()

    items = []
    for vk_user, customer in results:
        items.append({
            "vk_id": vk_user.vk_id,
            "phone": vk_user.phone,
            "first_name": vk_user.first_name,
            "last_name": vk_user.last_name,
            "photo_50": vk_user.photo_50,
            "screen_name": vk_user.screen_name,
            "linked_at": vk_user.linked_at,
            "is_subscribed": vk_user.is_subscribed,
            "notifications_enabled": vk_user.notifications_enabled,
            "is_blocked": vk_user.is_blocked,
            "customer": {
                "id": customer.id if customer else None,
                "name": customer.name if customer else None,
                "surname": customer.surname if customer else None
            } if customer else None
        })

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page
    }


@router.patch("/parser/linked-accounts/{vk_id}")
def update_linked_account_flags(
    vk_id: int,
    data: VkLinkedAccountUpdateSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_vk_parser_edit"))
):
    """Обновление флагов блокировки и разрешений уведомлений для связанного аккаунта"""
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if not vk_user:
        raise HTTPException(status_code=404, detail="Связанный аккаунт не найден")
    
    if data.is_blocked is not None:
        vk_user.is_blocked = data.is_blocked
    if data.notifications_enabled is not None:
        vk_user.notifications_enabled = data.notifications_enabled
        
    db.add(vk_user)
    db.commit()
    db.refresh(vk_user)
    return vk_user


@router.get("/connections/{connection_id}/diagnostics")
async def get_connection_diagnostics(
    connection_id: int,
    db: Session = Depends(get_session)
):
    """Диагностика токенов и прав VK API для подключения"""
    from app.services.vk_token_manager import get_vk_token_permissions_diagnostic, get_valid_user_token
    from app.models.vk_bot_connection import VkBotConnection
    from sqlmodel import select
    
    stmt = select(VkBotConnection).where(VkBotConnection.id == connection_id)
    conn = db.exec(stmt).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
        
    diag = await get_vk_token_permissions_diagnostic(conn.vk_bot_token, conn.vk_user_token)
    active_user_token = await get_valid_user_token(db, conn)
    diag["has_working_user_token"] = bool(active_user_token)
    diag["active_user_token_source"] = "auto_fallback" if active_user_token and active_user_token != conn.vk_user_token else ("direct" if active_user_token else "none")
    return diag
