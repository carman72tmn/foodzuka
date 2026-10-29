from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from app.core.database import get_session
from app.models.senler import SenlerSettings, SenlerSubscriber
from app.models.customer import Customer
from app.models.vk_user import VkUser
from app.services.senler_service import senler_service
from app.api.deps import require_permission
from app.models.user import User
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/senler", tags=["Senler Integration"])

# --- Схемы Pydantic ---

class SenlerSettingsSchema(BaseModel):
    id: Optional[int] = None
    access_token: Optional[str] = None
    group_id: Optional[int] = None
    vk_group_id: Optional[int] = None
    secret_key: Optional[str] = None
    is_active: bool = True

class TestConnectionRequest(BaseModel):
    access_token: str
    group_id: int

class CreateBroadcastRequest(BaseModel):
    name: str
    message: str
    subscription_id: int  # ID группы подписки Senler (0 - по всем)
    is_now: bool = True
    scheduled_time: Optional[int] = None  # Unix timestamp

class SubscriberResponse(BaseModel):
    id: int
    vk_user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_subscribed: bool
    subscribe_date: Optional[datetime] = None
    unsubscribe_date: Optional[datetime] = None
    group_ids: Optional[List[int]] = None
    utm_tags: Optional[Dict[str, str]] = None
    user_vars: Optional[Dict[str, str]] = None
    customer_id: Optional[int] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None

class PaginatedSubscribers(BaseModel):
    items: List[SubscriberResponse]
    total: int
    page: int
    size: int

# --- Эндпоинты ---

@router.get("/settings", response_model=SenlerSettingsSchema)
def get_senler_settings(
    db: Session = Depends(get_session), 
    current_user: User = Depends(require_permission("settings_senler_view"))
):
    """Получить настройки интеграции с Senler"""
    settings = db.exec(select(SenlerSettings)).first()
    if not settings:
        return SenlerSettingsSchema(is_active=False)
        
    # Маскируем токен для безопасности
    masked_token = None
    if settings.access_token:
        masked_token = settings.access_token[:4] + "..." + settings.access_token[-4:] if len(settings.access_token) > 8 else "***"
        
    return SenlerSettingsSchema(
        id=settings.id,
        access_token=masked_token,
        group_id=settings.group_id,
        vk_group_id=settings.vk_group_id,
        secret_key=settings.secret_key,
        is_active=settings.is_active
    )

@router.post("/settings", response_model=SenlerSettingsSchema)
def save_senler_settings(
    data: SenlerSettingsSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_senler_edit"))
):
    """Сохранить настройки интеграции с Senler"""
    settings = db.exec(select(SenlerSettings)).first()
    
    # Если токен пришел маскированным и настройки уже существуют, не меняем его
    access_token = data.access_token
    if settings and access_token and "..." in access_token:
        access_token = settings.access_token
        
    if settings:
        settings.access_token = access_token
        settings.group_id = data.group_id
        settings.vk_group_id = data.vk_group_id
        settings.secret_key = data.secret_key
        settings.is_active = data.is_active
    else:
        settings = SenlerSettings(
            access_token=access_token,
            group_id=data.group_id,
            vk_group_id=data.vk_group_id,
            secret_key=data.secret_key,
            is_active=data.is_active
        )
        db.add(settings)
        
    db.commit()
    db.refresh(settings)
    
    # Сгенерируем маскированный ответ
    masked_token = None
    if settings.access_token:
        masked_token = settings.access_token[:4] + "..." + settings.access_token[-4:] if len(settings.access_token) > 8 else "***"
        
    return SenlerSettingsSchema(
        id=settings.id,
        access_token=masked_token,
        group_id=settings.group_id,
        vk_group_id=settings.vk_group_id,
        secret_key=settings.secret_key,
        is_active=settings.is_active
    )

@router.post("/settings/test")
async def test_senler_connection(
    data: TestConnectionRequest,
    current_user: User = Depends(require_permission("settings_senler_edit")),
    db: Session = Depends(get_session)
):
    """Тест соединения с API Senler"""
    # Если пришел маскированный токен, берем оригинальный из базы
    token = data.access_token
    if "..." in token:
        settings = db.exec(select(SenlerSettings)).first()
        if settings:
            token = settings.access_token
            
    success = await senler_service.test_connection(token, data.group_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось подключиться к Senler. Проверьте правильность токена и ID группы.")
    return {"success": True, "message": "Соединение успешно установлено"}

@router.get("/groups")
async def get_senler_groups(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_senler_view"))
):
    """Получить список групп подписчиков из Senler"""
    try:
        groups = await senler_service.get_groups(db)
        return groups
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/subscribers", response_model=PaginatedSubscribers)
def get_subscribers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    group_id: Optional[int] = None,
    is_subscribed: Optional[bool] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_senler_view"))
):
    """Получить список локально импортированных подписчиков Senler"""
    query = select(SenlerSubscriber)
    
    # Фильтры
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (SenlerSubscriber.first_name.like(search_filter)) | 
            (SenlerSubscriber.last_name.like(search_filter)) |
            (func.cast(SenlerSubscriber.vk_user_id, func.text).like(search_filter))
        )
        
    if is_subscribed is not None:
        query = query.where(SenlerSubscriber.is_subscribed == is_subscribed)
        
    if group_id is not None:
        # Поскольку group_ids — это JSONB массив, используем оператор contains для PostgreSQL
        # В SQLAlchemy это можно записать как contains
        query = query.where(SenlerSubscriber.group_ids.contains([group_id]))

    # Общее количество
    total = db.exec(select(func.count()).select_from(query.subquery())).one()
    
    # Пагинация
    query = query.order_by(SenlerSubscriber.subscribe_date.desc()).offset((page - 1) * size).limit(size)
    subscribers = db.exec(query).all()
    
    # Собираем инфо о связи с Customer
    items = []
    for sub in subscribers:
        customer_info = db.exec(
            select(Customer.id, Customer.phone, Customer.name)
            .join(VkUser, VkUser.phone == Customer.phone)
            .where(VkUser.vk_id == sub.vk_user_id)
        ).first()
        
        customer_id = customer_info[0] if customer_info else None
        customer_phone = customer_info[1] if customer_info else None
        customer_name = customer_info[2] if customer_info else None
        
        items.append(SubscriberResponse(
            id=sub.id,
            vk_user_id=sub.vk_user_id,
            first_name=sub.first_name,
            last_name=sub.last_name,
            is_subscribed=sub.is_subscribed,
            subscribe_date=sub.subscribe_date,
            unsubscribe_date=sub.unsubscribe_date,
            group_ids=sub.group_ids,
            utm_tags=sub.utm_tags,
            user_vars=sub.user_vars,
            customer_id=customer_id,
            customer_phone=customer_phone,
            customer_name=customer_name
        ))
        
    return PaginatedSubscribers(
        items=items,
        total=total,
        page=page,
        size=size
    )

@router.post("/subscribers/sync")
def trigger_subscribers_sync(
    current_user: User = Depends(require_permission("settings_senler_edit"))
):
    """Запустить фоновую синхронизацию подписчиков Senler"""
    from app.tasks.senler_tasks import sync_senler_subscribers_task
    sync_senler_subscribers_task.delay()
    return {"status": "success", "message": "Синхронизация запущена в фоновом режиме"}

@router.get("/stats")
async def get_senler_stats(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_senler_view"))
):
    """Сводная статистика интеграции Senler"""
    try:
        # Локальные метрики
        total_subscribers = db.exec(select(func.count(SenlerSubscriber.id))).one()
        active_subscribers = db.exec(select(func.count(SenlerSubscriber.id)).where(SenlerSubscriber.is_subscribed == True)).one()
        
        # Получаем рассылки из Senler
        deliveries = await senler_service.get_deliveries(db)
        
        # Если есть рассылки, запросим по ним статистику
        delivery_stats_map = {}
        if deliveries:
            delivery_ids = [d["delivery_id"] for d in deliveries[:20]]  # Ограничим первыми 20 для скорости
            try:
                stats_res = await senler_service.get_delivery_stats(delivery_ids, db)
                # Результат обычно в формате { "delivery_id_1": { "sent": X, "read": Y, ... } }
                delivery_stats_map = stats_res
            except Exception as e:
                logger.warning(f"Failed to get deliveries stats from Senler: {e}")
                
        # Дополняем рассылки статистикой
        formatted_deliveries = []
        for d in deliveries:
            d_id = str(d["delivery_id"])
            stats = delivery_stats_map.get(d_id, {})
            formatted_deliveries.append({
                "delivery_id": d["delivery_id"],
                "name": d.get("name"),
                "date": d.get("date"),
                "status": d.get("status"), # 1 - черновик, 2 - в очереди, 3 - отправлено
                "sent": stats.get("sent", 0),
                "delivered": stats.get("delivered", 0),
                "read": stats.get("read", 0),
                "away": stats.get("away", 0)  # переходы
            })
            
        return {
            "total_subscribers": total_subscribers,
            "active_subscribers": active_subscribers,
            "deliveries": formatted_deliveries
        }
    except Exception as e:
        logger.error(f"Failed to get Senler stats: {e}")
        # Возвращаем локальную статистику если API недоступно
        total_subscribers = db.exec(select(func.count(SenlerSubscriber.id))).one()
        active_subscribers = db.exec(select(func.count(SenlerSubscriber.id)).where(SenlerSubscriber.is_subscribed == True)).one()
        return {
            "total_subscribers": total_subscribers,
            "active_subscribers": active_subscribers,
            "deliveries": [],
            "error": f"Ошибка запроса к API Senler: {str(e)}"
        }

@router.post("/broadcasts")
async def create_broadcast(
    data: CreateBroadcastRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_senler_edit"))
):
    """Создать и запустить рассылку в Senler"""
    try:
        res = await senler_service.create_delivery(
            name=data.name,
            message=data.message,
            subscription_id=data.subscription_id,
            is_now=data.is_now,
            scheduled_time=data.scheduled_time,
            db=db
        )
        return {"status": "success", "delivery_id": res.get("delivery_id"), "message": "Рассылка успешно создана в Senler"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
