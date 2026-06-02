from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.vk_settings import VkSettings
from app.models.vk_webhook_log import VkWebhookLog
from app.models.vk_message import VkMessage
from app.models.vk_user import VkUser
from app.services.vk_service import process_vk_event
from pydantic import BaseModel
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

class VkSettingsSchema(BaseModel):
    vk_bot_token: str | None = None
    vk_confirmation_code: str | None = None
    vk_group_id: str | None = None
    vk_secret_key: str | None = None
    vk_parser_enabled: bool = False
    vk_parser_phrase: str | None = None
    vk_parser_last_scan_at: Any | None = None
    vk_parser_scan_status: Dict[str, Any] | None = None
    vk_notification_settings: Dict[str, Any] | None = None

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
def start_historical_scan(db: Session = Depends(get_session)):
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
def get_scan_status(db: Session = Depends(get_session)):
    """Получение текущего статуса сканирования"""
    vk_settings = db.exec(select(VkSettings)).first()
    if not vk_settings:
        return {"status": "idle"}
    return vk_settings.vk_parser_scan_status or {"status": "idle"}

@router.get("/parser/stats")
def get_parser_stats(db: Session = Depends(get_session)):
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
def get_message_stats(date: str | None = None, db: Session = Depends(get_session)):
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
    db: Session = Depends(get_session)
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
def get_vk_settings(db: Session = Depends(get_session)):
    result = db.execute(select(VkSettings))
    settings_db = result.scalars().first()
    if not settings_db:
        return VkSettingsSchema()
    return settings_db

@router.post("/settings", response_model=VkSettingsSchema)
def save_vk_settings(data: VkSettingsSchema, db: Session = Depends(get_session)):
    result = db.execute(select(VkSettings))
    settings_db = result.scalars().first()
    
    if settings_db:
        settings_db.vk_bot_token = data.vk_bot_token
        settings_db.vk_confirmation_code = data.vk_confirmation_code
        settings_db.vk_group_id = data.vk_group_id
        settings_db.vk_secret_key = data.vk_secret_key
        settings_db.vk_parser_enabled = data.vk_parser_enabled
        settings_db.vk_parser_phrase = data.vk_parser_phrase
        settings_db.vk_notification_settings = data.vk_notification_settings
    else:
        settings_db = VkSettings(**data.model_dump())
        db.add(settings_db)
        
    db.commit()
    db.refresh(settings_db)
    return settings_db

@router.get("/test-connection")
async def test_vk_connection(db: Session = Depends(get_session)):
    """Проверка валидности токена бота"""
    result = db.execute(select(VkSettings))
    vk_settings = result.scalars().first()
    
    if not vk_settings or not vk_settings.vk_bot_token:
        raise HTTPException(status_code=400, detail="Токен бота не настроен")
        
    async with httpx.AsyncClient() as client:
        try:
            # Простейший запрос к API VK для проверки токена
            response = await client.get(
                "https://api.vk.com/method/groups.getById",
                params={
                    "access_token": vk_settings.vk_bot_token,
                    "v": "5.131"
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
    
    # Логируем входящее событие
    try:
        log_entry = VkWebhookLog(event_type=event_type or "unknown", payload=data)
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Ошибка при сохранении лога VK: {e}")

    result = db.execute(select(VkSettings))
    vk_settings = result.scalars().first()
    
    # Check secret key if configured
    if vk_settings and vk_settings.vk_secret_key and data.get("secret") != vk_settings.vk_secret_key:
        # Если это не подтверждение адреса, проверяем секрет
        if event_type != "confirmation":
            raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # Confirmation event
    if event_type == "confirmation":
        if not vk_settings or not vk_settings.vk_confirmation_code:
            return PlainTextResponse(content="ok")
        return PlainTextResponse(content=vk_settings.vk_confirmation_code)
    
    # Process other events
    bot_token = vk_settings.vk_bot_token if vk_settings else None
    try:
        await process_vk_event(data, db, bot_token)
    except Exception as e:
        logger.error(f"Error processing VK event: {e}")
        
    return PlainTextResponse(content="ok")

@router.get("/logs", response_model=List[VkLogResponse])
def get_vk_logs(limit: int = 50, db: Session = Depends(get_session)):
    """Получение последних событий VK"""
    result = db.execute(
        select(VkWebhookLog).order_by(VkWebhookLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()

@router.delete("/parser/users/{vk_id}/link")
def unlink_vk_user(vk_id: int, db: Session = Depends(get_session)):
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
def cleanup_old_messages(db: Session = Depends(get_session)):
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
