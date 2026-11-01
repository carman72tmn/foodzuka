"""
API эндпоинты для работы с заказами
"""
import asyncio
import json
import time
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta, date, timezone
from zoneinfo import ZoneInfo
from app.core.datetime_utils import utc_now
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlmodel import Session, select, func, or_
from app.models.employee import Shift
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from app.core.database import get_session
from app.models.company import Branch, Company
from app.models.customer import Customer
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductSize, ProductModifier
from app.models.promo_code import PromoCode
from app.models.action import Action
from app.models.iiko_settings import IikoSettings
from app.schemas import OrderCreate, OrderUpdate, OrderResponse, OrderItemResponse
import logging
from app.services.iiko_service import iiko_service
from app.services.iiko_sync_service import iiko_sync_service
from app.services.order_geo_service import geocode_order
from app.services.order_status_history_service import append_order_status_history
from app.api import deps
from app.models.user import User


logger = logging.getLogger(__name__)

# Кеш пользователей VK для устранения N+1 запросов при сериализации заказов
_vk_users_cache = None
_vk_users_cache_time = 0
_vk_users_cache_ttl = 60


def get_vk_users_cache(session: Session) -> Dict[str, Any]:
    global _vk_users_cache, _vk_users_cache_time
    now = time.time()
    if _vk_users_cache and (now - _vk_users_cache_time < _vk_users_cache_ttl):
        return _vk_users_cache

    from app.models.vk_user import VkUser
    try:
        vk_users = session.exec(select(VkUser).where(VkUser.is_linked == True)).all()
        vk_ids = set()
        phones = set()
        for u in vk_users:
            if u.vk_id:
                vk_ids.add(str(u.vk_id))
            if u.phone:
                clean_phone = "".join(filter(str.isdigit, str(u.phone)))
                if clean_phone:
                    phones.add(clean_phone)
                    if clean_phone.startswith("7") and len(clean_phone) == 11:
                        phones.add("8" + clean_phone[1:])
                    elif clean_phone.startswith("8") and len(clean_phone) == 11:
                        phones.add("7" + clean_phone[1:])
        _vk_users_cache = {
            "vk_ids": vk_ids,
            "phones": phones
        }
        _vk_users_cache_time = now
    except Exception as e:
        logger.error(f"Error caching vk_users: {e}")
        return {"vk_ids": set(), "phones": set()}
    return _vk_users_cache

# Кеш сопоставления курьеров для ускорения загрузки заказов
_couriers_mapping_cache = None
_couriers_mapping_cache_time = 0
_couriers_mapping_cache_ttl = 60  # Время жизни кеша - 60 секунд


def get_couriers_mapping(session: Session) -> Dict[str, Any]:
    global _couriers_mapping_cache, _couriers_mapping_cache_time
    now = time.time()
    
    if _couriers_mapping_cache and (now - _couriers_mapping_cache_time < _couriers_mapping_cache_ttl):
        return _couriers_mapping_cache

    from app.models.employee import Employee
    employees = session.exec(select(Employee)).all()
    
    # Кэшируем только простые типы данных (строки iiko_id и словари), полностью исключая DetachedInstanceError
    emp_by_name = {}
    for emp in employees:
        if emp.name:
            name_key = emp.name.lower().strip()
            emp_by_name[name_key] = str(emp.iiko_id) if emp.iiko_id else None
            
    users = session.exec(select(User).where(User.iiko_id != None)).all()
    user_by_iiko_id = {
        str(u.iiko_id): {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name
        } for u in users
    }
    
    users_all = session.exec(select(User)).all()
    user_by_name = {
        u.full_name.lower().strip(): {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name
        } for u in users_all if u.full_name
    }
    
    _couriers_mapping_cache = {
        "emp_by_name": emp_by_name,
        "user_by_iiko_id": user_by_iiko_id,
        "user_by_name": user_by_name
    }
    _couriers_mapping_cache_time = now
    
    return _couriers_mapping_cache


router = APIRouter(prefix="/orders", tags=["Orders"])


_active_couriers_response_cache: Optional[list] = None
_active_couriers_response_cache_time: float = 0.0
_active_couriers_lock = asyncio.Lock()


@router.get("/active-couriers")
async def get_active_couriers_for_orders(
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_view")),
):
    """
    Получить список активных курьеров строго с открытой сменой доставки в iiko (с кэшированием 15с и таймаутом 5с)
    """
    global _active_couriers_response_cache, _active_couriers_response_cache_time
    now = time.time()

    if _active_couriers_response_cache is not None and (now - _active_couriers_response_cache_time < 15):
        return {"status": "success", "data": _active_couriers_response_cache}

    async with _active_couriers_lock:
        now = time.time()
        if _active_couriers_response_cache is not None and (now - _active_couriers_response_cache_time < 15):
            return {"status": "success", "data": _active_couriers_response_cache}

        from app.models.employee import Employee
        
        logger.info(f"get_active_couriers_for_orders called by user: {current_user.username}")
        
        settings = session.exec(select(IikoSettings)).first()
        if not settings or not settings.organization_id:
            logger.warning("No iiko settings or organization ID configured.")
            return {"status": "success", "data": _active_couriers_response_cache or []}
            
        try:
            try:
                active_locations = await asyncio.wait_for(
                    iiko_service.get_active_couriers(organization_id=settings.organization_id),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning("iiko_service.get_active_couriers timed out (5s limit), using cache fallback")
                return {"status": "success", "data": _active_couriers_response_cache or []}

            logger.info(f"iiko get_active_couriers returned {len(active_locations) if active_locations else 0} locations: {active_locations}")
            
            db_couriers = session.exec(
                select(Employee).where(Employee.is_courier == True, Employee.status == "Active")
            ).all()
            courier_by_iiko_id = {c.iiko_id: c for c in db_couriers}
            
            data = []
            if active_locations:
                for loc in active_locations:
                    c_id = loc.get("id")
                    emp = courier_by_iiko_id.get(c_id)
                    if not emp:
                        emp = session.exec(select(Employee).where(Employee.iiko_id == c_id)).first()
                    if emp:
                        # Исключаем системные служебные аккаунты iiko
                        emp_name_lower = (emp.name or "").lower()
                        if any(bad in emp_name_lower for bad in ["iikotransport", "централизованн", "пользователь", "iikouser"]):
                            continue
                        data.append({
                            "id": emp.iiko_id,
                            "name": emp.name,
                            "phone": emp.phone,
                            "latitude": loc.get("latitude"),
                            "longitude": loc.get("longitude")
                        })
                    else:
                        logger.debug(f"Active courier ID {c_id} from iiko not found in DB, skipping.")
            
            # СТРОГО курьеры с открытой сменой доставки в iiko! Никаких фоллбэков на базу данных.
            logger.info(f"get_active_couriers_for_orders returning {len(data)} items: {data}")
            _active_couriers_response_cache = data
            _active_couriers_response_cache_time = time.time()
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"Error fetching active couriers for orders: {e}")
            return {"status": "error", "message": str(e), "data": _active_couriers_response_cache or []}



_cascades_cache = None
_cascades_cache_time = 0

def get_cached_cascades(session: Session) -> list:
    global _cascades_cache, _cascades_cache_time
    now = time.time()
    if _cascades_cache is not None and (now - _cascades_cache_time < 60):
        return _cascades_cache
        
    from app.models.mailing_cascade import MailingCascade
    from sqlalchemy.orm import selectinload
    try:
        cascades = session.exec(
            select(MailingCascade)
            .where(MailingCascade.is_active == True)
            .options(selectinload(MailingCascade.steps))
            .order_by(MailingCascade.id.desc())
        ).all()
        
        # Преобразуем в простые словари, чтобы не зависеть от ORM Session
        cached_list = []
        for c in cascades:
            steps_data = []
            if c.steps:
                for s in sorted(c.steps, key=lambda x: x.priority):
                    steps_data.append({
                        "id": s.id,
                        "priority": s.priority,
                        "channel": s.channel
                    })
            cached_list.append({
                "id": c.id,
                "trigger_event": c.trigger_event,
                "is_active": c.is_active,
                "order_type": c.order_type,
                "steps": steps_data
            })
            
        _cascades_cache = cached_list
        _cascades_cache_time = now
    except Exception as e:
        logger.error(f"Error caching cascades: {e}")
        return []
    return _cascades_cache


def enrich_order_social_and_notifications(
    order: Order, 
    session: Session, 
    vk_cache: Optional[Dict[str, Any]] = None,
    message_logs_by_order: Optional[Dict[int, Any]] = None
) -> Dict[str, Any]:
    from app.models.customer import Customer
    from app.models.vk_user import VkUser
    from app.models.message_log import CustomerMessageLog

    if vk_cache is None:
        vk_cache = get_vk_users_cache(session)
    vk_ids = vk_cache.get("vk_ids", set())
    vk_phones = vk_cache.get("phones", set())

    # 1. customer_social_channels
    customer = getattr(order, "customer", None)
    if not customer and order.customer_phone:
        customer = session.exec(select(Customer).where(Customer.phone == order.customer_phone)).first()

    has_vk = False
    has_tg = False
    has_max = False

    if customer:
        if getattr(customer, "vk_user_id", None) and str(customer.vk_user_id) in vk_ids:
            has_vk = True
        if not has_vk and getattr(customer, "phone", None):
            c_phone_digits = "".join(filter(str.isdigit, str(customer.phone)))
            if c_phone_digits in vk_phones:
                has_vk = True
        
        has_tg = bool(getattr(customer, "telegram_id", None))
        has_max = bool(getattr(customer, "max_user_id", None))
    else:
        if order.customer_phone:
            o_phone_digits = "".join(filter(str.isdigit, str(order.customer_phone)))
            if o_phone_digits in vk_phones:
                has_vk = True

    social_channels = {
        "vk": has_vk,
        "telegram": has_tg,
        "max": has_max
    }

    # 2. status_notification
    status_notification = {
        "configured": False,
        "channel": None,
        "status": None,
        "error_text": None
    }

    status_event_map = {
        OrderStatus.new: "new_order",
        OrderStatus.confirmed: "order_confirmed",
        OrderStatus.cooking: "order_cooking",
        OrderStatus.ready: "order_ready",
        OrderStatus.ready_for_pickup: "order_ready_for_pickup",
        OrderStatus.delivering: "order_delivering",
        OrderStatus.delivered: "order_delivered",
        OrderStatus.closed: "order_closed",
        OrderStatus.cancelled: "order_cancelled"
    }

    event_type = status_event_map.get(order.status)
    if event_type:
        all_cascades = get_cached_cascades(session)
        order_type_mapped = "delivery" if order.order_type == "Доставка" else "pickup"
        
        def match_cascade(c, ev):
            if c.get("trigger_event") != ev or not c.get("is_active"):
                return False
            c_type = c.get("order_type")
            if not c_type or c_type in ("any", order_type_mapped):
                return True
            return False

        cascade = next((c for c in all_cascades if match_cascade(c, event_type)), None)
        if not cascade and event_type == "order_ready_for_pickup":
            cascade = next((c for c in all_cascades if match_cascade(c, "order_ready")), None)

        if cascade:
            steps = cascade.get("steps") or []
            log = None
            if steps:
                step_ids = [s["id"] for s in steps]
                if message_logs_by_order is not None and order.id in message_logs_by_order:
                    # Быстрый поиск в оперативной памяти (0 мс)
                    candidate_logs = message_logs_by_order[order.id]
                    log = next((l for l in candidate_logs if l.get("cascade_step_id") in step_ids), None)
                else:
                    log_obj = session.exec(
                        select(CustomerMessageLog)
                        .where(
                            CustomerMessageLog.order_id == order.id,
                            CustomerMessageLog.cascade_step_id.in_(step_ids)
                        )
                        .order_by(CustomerMessageLog.id.desc())
                    ).first()
                    if log_obj:
                        log = {
                            "status": log_obj.status,
                            "channel": log_obj.channel,
                            "error_text": log_obj.error_text
                        }

            if log:
                log_status = log.get("status") if isinstance(log, dict) else log.status
                status_val = "success" if log_status in ("sent", "delivered", "read", "clicked") else ("failed" if log_status == "failed" else "not_sent")
                status_notification = {
                    "configured": True,
                    "channel": log.get("channel") if isinstance(log, dict) else log.channel,
                    "status": status_val,
                    "error_text": log.get("error_text") if isinstance(log, dict) else log.error_text
                }
            else:
                first_channel = steps[0]["channel"] if steps else None
                status_notification = {
                    "configured": True,
                    "channel": first_channel,
                    "status": "not_sent",
                    "error_text": None
                }

    return {
        "customer_social_channels": social_channels,
        "status_notification": status_notification
    }


# Серверный кэш обогащенных данных завершенных заказов
_archive_orders_cache: Dict[int, Dict[str, Any]] = {}
_MAX_ARCHIVE_CACHE_SIZE = 3000


def _invalidate_order_cache(order_id: int):
    """Сбросить кэш конкретного заказа при его изменении"""
    _archive_orders_cache.pop(order_id, None)


def _serialize_and_enrich_order(
    order: Order, 
    session: Session, 
    mapping: Dict[str, Any], 
    use_cache: bool = True,
    vk_cache: Optional[Dict[str, Any]] = None,
    message_logs_by_order: Optional[Dict[int, Any]] = None
) -> Dict[str, Any]:
    """
    Сериализует заказ в словарь, обогащает позициями, платежами,
    зонами, данными клиента, курьером и статусом соцсетей/уведомлений.
    Для завершенных заказов (closed, cancelled, delivered) использует быстрый серверный кэш.
    """
    is_completed = order.status in (OrderStatus.closed, OrderStatus.cancelled, OrderStatus.delivered)
    if use_cache and is_completed and order.id in _archive_orders_cache:
        return _archive_orders_cache[order.id]

    order_dict = order.model_dump()
    order_dict["items"] = [
        item.model_dump() if hasattr(item, "model_dump") else (dict(item) if isinstance(item, dict) else item)
        for item in (order.items or [])
    ]
    order_dict["total_paid"] = order.total_paid
    order_dict["resolved_delivery_zone_name"] = order.resolved_zone_name

    # Индикаторы клиента (приоритет снимку данных в заказе)
    if order.customer_info_details:
        order_dict["customer_is_new"] = order.customer_info_details.get("is_new_guest", False)
        order_dict["customer_is_risk"] = order.customer_info_details.get("is_high_risk", False)
    elif order.customer:
        order_dict["customer_is_new"] = getattr(order.customer, "is_new_guest", False)
        order_dict["customer_is_risk"] = getattr(order.customer, "is_high_risk", False)

    # Обогащаем социальными сетями и статусом уведомлений без N+1 запросов
    enriched = enrich_order_social_and_notifications(
        order, 
        session, 
        vk_cache=vk_cache, 
        message_logs_by_order=message_logs_by_order
    )
    order_dict.update(enriched)

    # Заполняем courier_user
    emp_by_name = mapping.get("emp_by_name", {})
    user_by_iiko_id = mapping.get("user_by_iiko_id", {})
    user_by_name = mapping.get("user_by_name", {})

    order_dict["courier_user"] = None
    if order.courier_name and order.courier_name != "Не назначен":
        c_name_key = order.courier_name.lower().strip()
        emp_iiko_id = emp_by_name.get(c_name_key)
        user_data = None
        if emp_iiko_id:
            user_data = user_by_iiko_id.get(str(emp_iiko_id))
        if not user_data:
            user_data = user_by_name.get(c_name_key)
        if user_data:
            order_dict["courier_user"] = user_data

    # Если заказ завершен, сохраняем в серверный кэш
    if is_completed and order.id:
        if len(_archive_orders_cache) >= _MAX_ARCHIVE_CACHE_SIZE:
            # Очищаем треть старейших записей
            keys_to_remove = list(_archive_orders_cache.keys())[:1000]
            for k in keys_to_remove:
                _archive_orders_cache.pop(k, None)
        _archive_orders_cache[order.id] = order_dict

    return order_dict


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[OrderStatus] = None,
    telegram_user_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_view")),
):
    """
    Получить список заказов с ультрабыстрой отдачей через JSONResponse и пакетную оптимизацию
    """
    query = select(Order).options(
        selectinload(Order.resolved_zone),
        selectinload(Order.customer),
        selectinload(Order.items)  # Подгружаем позиции сразу
    ).order_by(Order.created_at.desc()).offset(skip).limit(limit)

    if status_filter:
        query = query.where(Order.status == status_filter)

    if telegram_user_id:
        query = query.where(Order.telegram_user_id == telegram_user_id)

    orders = session.exec(query).all()
    mapping = get_couriers_mapping(session)
    vk_cache = get_vk_users_cache(session)

    # Пакетная предзагрузка логов рассылок для исключения N+1 SQL-запросов
    order_ids = [o.id for o in orders if o.id]
    message_logs_by_order: Dict[int, list] = {}
    if order_ids:
        from app.models.message_log import CustomerMessageLog
        try:
            recent_logs = session.exec(
                select(
                    CustomerMessageLog.order_id, 
                    CustomerMessageLog.cascade_step_id, 
                    CustomerMessageLog.channel, 
                    CustomerMessageLog.status, 
                    CustomerMessageLog.error_text
                )
                .where(CustomerMessageLog.order_id.in_(order_ids))
                .order_by(CustomerMessageLog.id.desc())
            ).all()
            for r in recent_logs:
                oid = r[0]
                if oid not in message_logs_by_order:
                    message_logs_by_order[oid] = []
                message_logs_by_order[oid].append({
                    "cascade_step_id": r[1],
                    "channel": r[2],
                    "status": r[3],
                    "error_text": r[4]
                })
        except Exception as log_err:
            logger.warning(f"Failed to batch load CustomerMessageLog: {log_err}")

    enriched = [
        _serialize_and_enrich_order(
            order, 
            session, 
            mapping, 
            use_cache=True,
            vk_cache=vk_cache,
            message_logs_by_order=message_logs_by_order
        ) 
        for order in orders
    ]
    return JSONResponse(content=jsonable_encoder(enriched))


@router.get("/active", response_model=List[OrderResponse])
def get_active_orders(
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_view")),
):
    """
    Получить только активные заказы (в работе).
    Исключает закрытые, отмененные и доставленные заказы.
    Отрабатывает за 5-15 мс для мгновенной подгрузки заказов в работе.
    """
    active_statuses = [
        OrderStatus.new,
        OrderStatus.unconfirmed,
        OrderStatus.confirmed,
        OrderStatus.preparing,
        OrderStatus.cooking,
        OrderStatus.ready,
        OrderStatus.ready_for_pickup,
        OrderStatus.delivering,
    ]
    query = (
        select(Order)
        .options(
            selectinload(Order.resolved_zone),
            selectinload(Order.customer),
            selectinload(Order.items),
        )
        .where(Order.status.in_(active_statuses))
        .order_by(Order.created_at.desc())
    )
    orders = session.exec(query).all()
    mapping = get_couriers_mapping(session)
    vk_cache = get_vk_users_cache(session)
    enriched = [
        _serialize_and_enrich_order(
            order, 
            session, 
            mapping, 
            use_cache=False,
            vk_cache=vk_cache
        ) 
        for order in orders
    ]
    return JSONResponse(content=jsonable_encoder(enriched))


@router.get("/dashboard-summary")
def get_dashboard_summary(session: Session = Depends(get_session)):
    """
    Агрегированные данные для главной страницы панели администратора (Дашборд).
    Все показатели рассчитываются из реальных данных базы данных (заказы, смены).
    """
    try:
        try:
            tz = ZoneInfo("Asia/Yekaterinburg")
        except Exception:
            tz = timezone(timedelta(hours=5))
            
        now_local = datetime.now(tz)
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        today_date = today_start_local.date()
        yesterday_date = today_date - timedelta(days=1)
        
        def to_naive_utc(dt: datetime) -> datetime:
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt

        def to_local(dt: datetime) -> datetime:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc).astimezone(tz)
            return dt.astimezone(tz)

        def get_order_actual_revenue(o: Order) -> float:
            """
            Поступление средств в кассу за уже оплаченный заказ на текущий день
            с вычетом скидок и бонусов.
            Считаются только заказы, которые уже оплачены (is_paid, статус closed/delivered или внесенная оплата).
            """
            if o.status == OrderStatus.cancelled:
                return 0.0
            
            is_fully_paid = bool(o.is_paid) or o.status in (OrderStatus.closed, OrderStatus.delivered)
            paid_sum = float(o.total_paid or 0.0)
            with_disc = float(o.total_with_discount if o.total_with_discount is not None else (o.total_amount or 0.0))
            
            if is_fully_paid:
                return paid_sum if paid_sum > 0 else with_disc
            
            # Если частичная оплата на кассе/онлайн уже зафиксирована
            if paid_sum > 0:
                return paid_sum
                
            return 0.0

        def get_order_expected_revenue(o: Order) -> float:
            """
            Ожидаемая выручка от заказа с учетом скидок и оплаты бонусами
            (вся сумма к оплате деньгами, которая поступит при полной оплате заказа).
            """
            if o.status == OrderStatus.cancelled:
                return 0.0
            if o.total_with_discount is not None:
                return float(o.total_with_discount)
            if o.total_amount is not None:
                return float(o.total_amount)
            return 0.0

        def is_order_paid(o: Order) -> bool:
            """Оплачен ли заказ (полностью или доставлен/закрыт в iiko)"""
            if o.status == OrderStatus.cancelled:
                return False
            return (
                bool(o.is_paid) 
                or o.status in (OrderStatus.closed, OrderStatus.delivered)
                or (float(o.total_paid or 0.0) >= float(o.total_with_discount or o.total_amount or 0.0) > 0)
            )

        def get_order_business_date(o: Order) -> date:
            """
            Учетный день заказа:
            Для предзаказов на будущую дату (не ASAP и есть expected_time) учет ведется
            по дате исполнения (expected_time). Для обычных заказов - по дате создания.
            """
            if not o.is_asap and o.expected_time:
                return to_local(o.expected_time).date()
            return to_local(o.created_at).date()

        today_start_utc_naive = to_naive_utc(today_start_local)
        week_start_utc_naive = today_start_utc_naive - timedelta(days=6)
        
        # 1. Заказы за рассматриваемый период (включая возможные предзаказы, сделанные заранее)
        orders_pool = session.exec(
            select(Order)
            .where(
                or_(
                    Order.created_at >= week_start_utc_naive - timedelta(days=7),
                    Order.expected_time >= week_start_utc_naive
                ),
                Order.status != OrderStatus.cancelled
            )
            .order_by(Order.created_at.asc())
        ).all()
        
        # Разделяем на сегодня и вчера по учетной дате заказа
        today_orders = [o for o in orders_pool if get_order_business_date(o) == today_date]
        yesterday_orders = [o for o in orders_pool if get_order_business_date(o) == yesterday_date]
        
        # Метрики Сегодня (Текущая фактическая выручка в кассе vs Ожидаемая с учетом неоплаченных)
        today_actual_rev = sum(get_order_actual_revenue(o) for o in today_orders)
        today_expected_rev = sum(get_order_expected_revenue(o) for o in today_orders)
        today_unpaid_rev = max(0.0, today_expected_rev - today_actual_rev)
        
        today_cnt = len(today_orders)
        today_paid_cnt = sum(1 for o in today_orders if is_order_paid(o))
        today_unpaid_cnt = today_cnt - today_paid_cnt
        
        today_avg = round(today_actual_rev / today_paid_cnt, 2) if today_paid_cnt > 0 else (round(today_expected_rev / today_cnt, 2) if today_cnt > 0 else 0.0)
        active_cnt = sum(1 for o in today_orders if o.status not in (OrderStatus.delivered, OrderStatus.closed, OrderStatus.cancelled))
        delivered_cnt = sum(1 for o in today_orders if o.status in (OrderStatus.delivered, OrderStatus.closed))
        
        # Метрики Вчера
        yesterday_actual_rev = sum(get_order_actual_revenue(o) for o in yesterday_orders)
        yesterday_expected_rev = sum(get_order_expected_revenue(o) for o in yesterday_orders)
        yesterday_cnt = len(yesterday_orders)
        yesterday_paid_cnt = sum(1 for o in yesterday_orders if is_order_paid(o))
        yesterday_avg = round(yesterday_actual_rev / yesterday_paid_cnt, 2) if yesterday_paid_cnt > 0 else (round(yesterday_expected_rev / yesterday_cnt, 2) if yesterday_cnt > 0 else 0.0)
        
        # Динамика % к вчера
        def calc_change(current: float, previous: float) -> float:
            if previous > 0:
                return round(((current - previous) / previous) * 100, 1)
            return 100.0 if current > 0 else 0.0

        rev_change = calc_change(today_actual_rev, yesterday_actual_rev)
        expected_rev_change = calc_change(today_expected_rev, yesterday_expected_rev)
        cnt_change = calc_change(float(today_cnt), float(yesterday_cnt))
        avg_change = calc_change(today_avg, yesterday_avg)
        
        # 2. Недельный тренд по дням (7 дней)
        weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        daily_trend = []
        for i in range(7):
            d_local = (today_start_local - timedelta(days=6 - i)).date()
            daily_trend.append({
                "date": d_local.strftime("%d.%m"),
                "full_date": str(d_local),
                "day_name": weekday_names[d_local.weekday()],
                "revenue": 0.0,
                "expected_revenue": 0.0,
                "orders_count": 0,
                "is_today": (d_local == today_date)
            })
            
        trend_map = {item["full_date"]: item for item in daily_trend}
        for o in orders_pool:
            d_str = str(get_order_business_date(o))
            if d_str in trend_map:
                trend_map[d_str]["orders_count"] += 1
                trend_map[d_str]["revenue"] += get_order_actual_revenue(o)
                trend_map[d_str]["expected_revenue"] += get_order_expected_revenue(o)
                
        for item in daily_trend:
            item["revenue"] = round(item["revenue"], 2)
            item["expected_revenue"] = round(item["expected_revenue"], 2)
            
        week_total_rev = round(sum(item["revenue"] for item in daily_trend), 2)
        week_total_expected_rev = round(sum(item["expected_revenue"] for item in daily_trend), 2)
        week_total_orders = sum(item["orders_count"] for item in daily_trend)
        
        # 3. Распределение по типам заказа (7 дней)
        orders_7d_actual = [o for o in orders_pool if str(get_order_business_date(o)) in trend_map]
        delivery_orders = [o for o in orders_7d_actual if o.order_type == "Доставка"]
        pickup_orders = [o for o in orders_7d_actual if o.order_type == "Самовывоз"]
        other_orders = [o for o in orders_7d_actual if o.order_type not in ("Доставка", "Самовывоз")]
        
        deliv_rev = sum(get_order_actual_revenue(o) for o in delivery_orders)
        pickup_rev = sum(get_order_actual_revenue(o) for o in pickup_orders)
        other_rev = sum(get_order_actual_revenue(o) for o in other_orders)
        
        deliv_expected = sum(get_order_expected_revenue(o) for o in delivery_orders)
        pickup_expected = sum(get_order_expected_revenue(o) for o in pickup_orders)
        other_expected = sum(get_order_expected_revenue(o) for o in other_orders)
        
        # 4. Последние 8 заказов (для виджета транзакций)
        recent_orders_db = session.exec(
            select(Order)
            .order_by(Order.created_at.desc())
            .limit(8)
        ).all()
        
        status_translations = {
            OrderStatus.new: "Новый",
            OrderStatus.unconfirmed: "Не подтвержден",
            OrderStatus.confirmed: "Подтвержден",
            OrderStatus.cooking: "Готовится",
            OrderStatus.preparing: "В сборке",
            OrderStatus.ready: "Готов",
            OrderStatus.ready_for_pickup: "Готов к выдаче",
            OrderStatus.delivering: "В пути",
            OrderStatus.delivered: "Доставлен",
            OrderStatus.closed: "Закрыт",
            OrderStatus.cancelled: "Отменен",
        }
        
        recent_transactions = []
        for o in recent_orders_db:
            created_local = to_local(o.created_at)
            status_ru = status_translations.get(o.status, str(o.status.value if hasattr(o.status, "value") else o.status))
            actual_amount = get_order_actual_revenue(o)
            expected_amount = get_order_expected_revenue(o)
            recent_transactions.append({
                "id": o.id,
                "order_number": o.external_number or str(o.id),
                "customer_name": o.customer_name or "Гость",
                "customer_phone": o.customer_phone or "",
                "amount": actual_amount if actual_amount > 0 else expected_amount,
                "actual_amount": actual_amount,
                "expected_amount": expected_amount,
                "payment_method": o.payment_method or "Не указан",
                "order_type": o.order_type or "Доставка",
                "status": o.status.value if hasattr(o.status, "value") else str(o.status),
                "status_ru": status_ru,
                "is_paid": bool(o.is_paid),
                "time": created_local.strftime("%H:%M"),
                "date": created_local.strftime("%d.%m"),
            })
            
        # 5. Сотрудники на смене (только открытые за последние 24 часа)
        cutoff_14h = datetime.now(timezone.utc) - timedelta(hours=14)
        open_shifts_count = session.exec(
            select(func.count(Shift.id)).where(
                Shift.status == "OPEN",
                Shift.date_open >= cutoff_14h
            )
        ).one() or 0

        return {
            "status": "success",
            "today": {
                "revenue": round(today_actual_rev, 2),
                "revenue_formatted": f"{int(round(today_actual_rev)):,} ₽".replace(",", " "),
                "expected_revenue": round(today_expected_rev, 2),
                "expected_revenue_formatted": f"{int(round(today_expected_rev)):,} ₽".replace(",", " "),
                "unpaid_revenue": round(today_unpaid_rev, 2),
                "unpaid_revenue_formatted": f"{int(round(today_unpaid_rev)):,} ₽".replace(",", " "),
                "orders_count": today_cnt,
                "paid_orders_count": today_paid_cnt,
                "unpaid_orders_count": today_unpaid_cnt,
                "average_check": round(today_avg, 2),
                "average_check_formatted": f"{int(round(today_avg)):,} ₽".replace(",", " "),
                "active_orders": active_cnt,
                "delivered_orders": delivered_cnt,
            },
            "yesterday": {
                "revenue": round(yesterday_actual_rev, 2),
                "revenue_formatted": f"{int(round(yesterday_actual_rev)):,} ₽".replace(",", " "),
                "expected_revenue": round(yesterday_expected_rev, 2),
                "expected_revenue_formatted": f"{int(round(yesterday_expected_rev)):,} ₽".replace(",", " "),
                "orders_count": yesterday_cnt,
                "paid_orders_count": yesterday_paid_cnt,
                "unpaid_orders_count": yesterday_cnt - yesterday_paid_cnt,
                "average_check": round(yesterday_avg, 2),
                "average_check_formatted": f"{int(round(yesterday_avg)):,} ₽".replace(",", " "),
            },
            "growth": {
                "revenue_change": rev_change,
                "expected_revenue_change": expected_rev_change,
                "orders_change": cnt_change,
                "average_check_change": avg_change,
            },
            "week_summary": {
                "total_revenue": week_total_rev,
                "total_revenue_formatted": f"{int(round(week_total_rev)):,} ₽".replace(",", " "),
                "total_expected_revenue": week_total_expected_rev,
                "total_expected_revenue_formatted": f"{int(round(week_total_expected_rev)):,} ₽".replace(",", " "),
                "total_orders": week_total_orders,
                "daily_trend": daily_trend,
            },
            "order_types": {
                "delivery": {
                    "count": len(delivery_orders),
                    "revenue": round(deliv_rev, 2),
                    "revenue_formatted": f"{int(round(deliv_rev)):,} ₽".replace(",", " "),
                    "expected_revenue": round(deliv_expected, 2),
                    "expected_revenue_formatted": f"{int(round(deliv_expected)):,} ₽".replace(",", " "),
                },
                "pickup": {
                    "count": len(pickup_orders),
                    "revenue": round(pickup_rev, 2),
                    "revenue_formatted": f"{int(round(pickup_rev)):,} ₽".replace(",", " "),
                    "expected_revenue": round(pickup_expected, 2),
                    "expected_revenue_formatted": f"{int(round(pickup_expected)):,} ₽".replace(",", " "),
                },
                "other": {
                    "count": len(other_orders),
                    "revenue": round(other_rev, 2),
                    "expected_revenue": round(other_expected, 2),
                },
                "total_count": len(orders_7d_actual),
            },
            "recent_transactions": recent_transactions,
            "open_shifts_count": int(open_shifts_count),
            "updated_at": now_local.strftime("%H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error calculating dashboard summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка формирования дашборда: {str(e)}")


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_view")),
):
    """Получить заказ по ID"""
    order = session.exec(select(Order).options(
        selectinload(Order.resolved_zone),
        selectinload(Order.customer),
        selectinload(Order.items)
    ).where(Order.id == order_id)).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    mapping = get_couriers_mapping(session)
    return _serialize_and_enrich_order(order, session, mapping, use_cache=False)



@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):

    """
    Создать новый заказ

    1. Проверяем наличие товаров
    2. Вычисляем общую сумму
    3. Создаем заказ в БД
    4. Отправляем заказ в iiko
    """
    # Проверяем клиента и создаем/обновляем карточку (Черный список)
    order_info = f"Заказ с сайта/бота на адрес: {order_data.delivery_address}"
    if order_data.comment:
        order_info += f" | Коммент: {order_data.comment}"
        
    customer_id = await iiko_sync_service.ensure_customer_from_order(
        phone=order_data.customer_phone,
        name=order_data.customer_name,
        surname=order_data.customer_surname,
        order_info=order_info,
        order_date=datetime.now(),
        telegram_id=order_data.telegram_user_id
    )
    
    customer = await asyncio.to_thread(session.get, Customer, customer_id)
    if not customer:
        # Резервный вариант на случай ошибки в методе
        customer = await asyncio.to_thread(lambda: session.exec(select(Customer).where(Customer.phone == order_data.customer_phone)).first())
    
    if customer.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш аккаунт заблокирован. Пожалуйста, свяжитесь с поддержкой."
        )

    # Данные лояльности уже синхронизированы внутри ensure_customer_from_order
    # Обновляем объект из базы, чтобы получить актуальный баланс бонусов и UID
    await asyncio.to_thread(session.refresh, customer)

    # Проверяем возможность списания бонусов
    bonus_spent = Decimal("0.00")
    if order_data.bonus_spent and order_data.bonus_spent > 0:
        if order_data.bonus_spent > customer.bonus_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно бонусов. Доступно: {customer.bonus_points}"
            )
        bonus_spent = order_data.bonus_spent

    # Обработка промокода
    promo_code_id = None
    promo_discount = Decimal("0.00")
    
    if order_data.promo_code:
        promo = await asyncio.to_thread(lambda: session.exec(select(PromoCode).where(PromoCode.code == order_data.promo_code)).first())
        if not promo or not promo.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Промокод не найден или неактивен"
            )
        
        # Проверка дат
        today = utc_now().date()
        if (promo.valid_from and today < promo.valid_from) or (promo.valid_until and today > promo.valid_until):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Срок действия промокода истек или еще не наступил"
            )
        
        # Проверка лимита использований
        if promo.max_uses is not None and promo.current_uses >= promo.max_uses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Промокод больше не действителен (превышен лимит использований)"
            )
        
        # Проверка "один раз для клиента"
        if promo.usage_type == "single_per_user":
            existing_order = await asyncio.to_thread(lambda: session.exec(
                select(Order).where(Order.customer_id == customer.id, Order.promo_code_id == promo.id)
            ).first())
            if existing_order:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Вы уже использовали этот промокод"
                )
        
        # Проверка "только первый заказ"
        if promo.first_order_only and customer.total_orders_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Промокод доступен только для первого заказа"
            )
        
        promo_code_id = promo.id
        # Логика расчета скидки (процент или фикс) будет ниже после расчета base total

    # Проверяем филиал
    branch = await asyncio.to_thread(session.get, Branch, order_data.branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Branch with id {order_data.branch_id} not found"
        )
    if not branch.is_active or not branch.is_accepting_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Branch '{branch.name}' is currently not accepting orders"
        )

    # Проверяем товары и вычисляем сумму
    total_amount = Decimal("0.00")
    order_items_data = []

    for item in order_data.items:
        product = await asyncio.to_thread(session.get, Product, item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item.product_id} not found"
            )
        if not product.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is not available"
            )

        item_price = product.price
        size_name = None
        product_iiko_id = product.iiko_id

        if item.product_size_id:
            size = await asyncio.to_thread(session.get, ProductSize, item.product_size_id)
            if not size or size.product_id != product.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ProductSize with id {item.product_size_id} not found for product {product.id}"
                )
            item_price = size.price
            size_name = size.name
            product_iiko_id = size.iiko_id

        modifier_details = []
        if item.modifiers:
            for mod_data in item.modifiers:
                mod_id = mod_data.get("modifier_id")
                mod_qty = mod_data.get("quantity", 1)
                modifier = await asyncio.to_thread(session.get, ProductModifier, mod_id)
                if not modifier:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"ProductModifier with id {mod_id} not found"
                    )
                item_price += modifier.price * mod_qty
                modifier_details.append({
                    "id": modifier.id,
                    "name": modifier.name,
                    "price": float(modifier.price),
                    "quantity": mod_qty,
                    "iiko_id": modifier.iiko_id
                })

        item_total = item_price * item.quantity
        total_amount += item_total

        order_items_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "price": item_price,
            "total": item_total,
            "size_name": size_name,
            "modifiers": modifier_details,
            "product_iiko_id": product_iiko_id
        })

    # Скидка (бонусы + промокод)
    total_discount = bonus_spent
    
    # 1. Применяем промокод
    if promo_code_id:
        promo = await asyncio.to_thread(session.get, PromoCode, promo_code_id)
        if promo.promo_type == "percent":
            promo_discount = (total_amount * promo.discount_value / Decimal("100")).quantize(Decimal("0.01"))
        elif promo.promo_type == "fixed":
            promo_discount = promo.discount_value
        
        # Лимит скидки по промокоду (не может быть больше суммы заказа)
        promo_discount = min(promo_discount, total_amount - total_discount)
        total_discount += promo_discount
        
        # Обновляем счетчик использований промокода
        promo.current_uses += 1
        await asyncio.to_thread(lambda: (session.add(promo), session.flush()))

    # 2. Проверяем наличие подарков по акциям
    actions = session.exec(select(Action).where(Action.is_active == True)).all()
    for action in actions:
        # Простая проверка суммы для примера (gift_product)
        if action.action_type == "gift_product" and action.min_order_amount:
            if total_amount >= action.min_order_amount:
                # Добавляем подарок в позиции заказа
                import json
                try:
                    gift_ids = json.loads(action.gift_product_ids) if action.gift_product_ids else []
                    for g_id in gift_ids:
                        gift_product = await asyncio.to_thread(session.get, Product, g_id)
                        if gift_product:
                            order_items_data.append({
                                "product_id": gift_product.id,
                                "product_name": f"ПОДАРОК: {gift_product.name}",
                                "quantity": 1,
                                "price": Decimal("0.00"),
                                "total": Decimal("0.00")
                            })
                except Exception as e:
                    print(f"Error processing gift action: {e}")

    # Итоговая сумма к оплате не может быть меньше 0
    final_total = max(total_amount - total_discount, Decimal("0.00"))

    # Создаем заказ
    order = Order(
        telegram_user_id=order_data.telegram_user_id,
        telegram_username=order_data.telegram_username,
        branch_id=order_data.branch_id,
        customer_id=customer.id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        delivery_address=order_data.delivery_address,
        total_amount=final_total,
        bonus_spent=bonus_spent,
        total_discount=total_discount,
        promo_code_id=promo_code_id,
        comment=order_data.comment,
        status=OrderStatus.new
    )
    append_order_status_history(
        order=order,
        new_status=OrderStatus.new,
        session=session,
        comment="Заказ принят (создан клиентом)"
    )
    def _save_order():
        session.add(order)
        session.commit()
        session.refresh(order)

        # Создаем позиции заказа
        for item_data in order_items_data:
            db_item_data = item_data.copy()
            db_item_data.pop("product_iiko_id", None)
            order_item = OrderItem(order_id=order.id, **db_item_data)
            session.add(order_item)

        session.commit()
    
    await asyncio.to_thread(_save_order)
    
    # Фоновое геокодирование
    background_tasks.add_task(geocode_order, order.id, lambda: Session(session.bind))


    # Отправляем заказ в iiko (асинхронно, не блокируем ответ)
    try:
        iiko_items = [
            {
                "product_id": item.get("product_iiko_id") or item["product_id"],
                "quantity": item["quantity"],
                "price": item["price"],
                "modifiers": item.get("modifiers", [])
            }
            for item in order_items_data
        ]

        # Подготавливаем данные для скидок в iiko
        discount_info = None
        if order.bonus_spent > 0:
            discount_info = {
                "discounts": [
                    {
                        "type": "iikoCard",
                        "sum": float(order.bonus_spent)
                    }
                ]
            }

        iiko_response = await iiko_service.create_delivery_order(
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            address=order.delivery_address,
            items=iiko_items,
            comment=order.comment,
            discount_info=discount_info
        )

        # Сохраняем ID заказа из iiko
        if iiko_response.get("orderId"):
            def _update_iiko_id():
                order.iiko_order_id = iiko_response["orderId"]
                order.status = OrderStatus.confirmed
                append_order_status_history(
                    order=order,
                    new_status=OrderStatus.confirmed,
                    session=session,
                    comment="Подтвержден iiko Cloud"
                )
                session.add(order)
                session.commit()
            await asyncio.to_thread(_update_iiko_id)
    except Exception as e:
        # Логируем ошибку, но не блокируем создание заказа
        print(f"Error sending order to iiko: {e}")

    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order.id)
    order_dict = order.model_dump()
    order_dict["items"] = list(await asyncio.to_thread(lambda: session.exec(items_query).all()))
    # Явно добавляем имя зоны доставки из property
    order_dict["resolved_delivery_zone_name"] = order.resolved_zone_name

    return order_dict


@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_edit")),
):

    """Обновить заказ"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    # Фиксируем старые значения для уведомлений курьера
    old_status = order.status
    old_address = order.delivery_address
    old_amount = float(order.total_with_discount or order.total_amount or 0)
    old_expected_time = order.expected_time
    old_courier = order.courier_name

    # Обновляем только предоставленные поля
    update_data = order_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    session.add(order)
    session.commit()
    session.refresh(order)
    _invalidate_order_cache(order_id)
    
    # Если адрес изменился, пересчитываем геопозицию
    if order_data.delivery_address:
        background_tasks.add_task(geocode_order, order.id, lambda: Session(session.bind))

    # Проверка цепочек уведомлений курьеру при ручном изменении в админке
    try:
        from app.services.iiko_sync_service import iiko_sync_service
        # 1. Изменение адреса
        if order_data.delivery_address and old_address != order.delivery_address:
            background_tasks.add_task(
                run_sync_with_session,
                iiko_sync_service.send_order_notification,
                order,
                "order_address_changed"
            )
        # 2. Изменение суммы
        new_amount = float(order.total_with_discount or order.total_amount or 0)
        if abs(new_amount - old_amount) > 0.01 and old_amount > 0:
            background_tasks.add_task(
                run_sync_with_session,
                iiko_sync_service.send_order_notification,
                order,
                "order_amount_changed"
            )
        # 3. Изменение времени доставки
        if order_data.expected_time and old_expected_time != order.expected_time:
            background_tasks.add_task(
                run_sync_with_session,
                iiko_sync_service.send_order_notification,
                order,
                "order_time_changed"
            )
        # 4. Изменение статуса
        if order_data.status and old_status != order.status:
            background_tasks.add_task(
                run_sync_with_session,
                iiko_sync_service.send_order_notification,
                order,
                "order_status_update"
            )
        # 5. Назначение или переназначение курьера
        if order.courier_name and order.courier_name != "Не назначен" and order.courier_name != old_courier:
            is_reassigned = bool(old_courier and old_courier != "Не назначен")
            background_tasks.add_task(
                run_sync_with_session,
                iiko_sync_service.send_order_notification,
                order,
                "courier_assigned"
            )
            if is_reassigned:
                background_tasks.add_task(
                    run_sync_with_session,
                    iiko_sync_service.send_order_notification,
                    order,
                    "order_new"
                )
    except Exception as e_notify:
        logger.error(f"Error scheduling order change notification from update_order: {e_notify}")

    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())

    return order_dict


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_edit")),
):
    """Отменить заказ"""
    order = await asyncio.to_thread(session.get, Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    if order.status in [OrderStatus.delivered, OrderStatus.cancelled]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status {order.status}"
        )

    # Отменяем в iiko
    if order.iiko_order_id:
        try:
            await iiko_service.cancel_order(order.iiko_order_id)
        except Exception as e:
            print(f"Error cancelling order in iiko: {e}")

    # Обновляем статус
    def _update_status():
        order.status = OrderStatus.cancelled
        append_order_status_history(
            order=order,
            new_status=OrderStatus.cancelled,
            session=session,
            comment="Отменен"
        )
        session.add(order)
        session.commit()
        session.refresh(order)
        _invalidate_order_cache(order_id)
    await asyncio.to_thread(_update_status)

    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())

    return order_dict
    
@router.get("/by-phone/{phone}", response_model=List[OrderResponse])
def get_orders_by_phone(
    phone: str, 
    skip: int = Query(0, ge=0),
    limit: int = Query(7, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """Получить локальные заказы по номеру телефона клиента с пагинацией"""
    from app.utils.phone_utils import normalize_phone
    normalized = normalize_phone(phone)
    query = select(Order).where(Order.customer_phone == normalized).order_by(Order.created_at.desc()).offset(skip).limit(limit)
    orders = session.exec(query).all()
    
    # Добавляем позиции к каждому заказу
    result = []
    for order in orders:
        items_query = select(OrderItem).where(OrderItem.order_id == order.id)
        order_dict = order.model_dump()
        order_dict["items"] = list(session.exec(items_query).all())
        # Явно добавляем имя зоны доставки из property
        order_dict["resolved_delivery_zone_name"] = order.resolved_zone_name
        result.append(order_dict)
        
    return result


# --- IIKO INTEGRATION ---

@router.post("/webhook/iiko")
async def iiko_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Прием вебхука от iiko Cloud (с валидацией токена).
    Использует background_tasks для синхронизации, чтобы не блокировать iiko.
    """
    from app.models.iiko_settings import IikoSettings
    settings = session.exec(select(IikoSettings)).first()
    expected_token = settings.webhook_auth_token if settings else None
    if expected_token:
        auth_header = request.headers.get("Authorization") or request.headers.get("X-Iiko-Token") or request.query_params.get("token")
        if auth_header and auth_header.startswith("Bearer "):
            auth_header = auth_header[7:]
        if auth_header != expected_token:
            logger.warning("Unauthorized access to /orders/webhook/iiko")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Error parsing webhook JSON: {e}")
        return {"status": "error", "message": "invalid json"}

    if not isinstance(data, list):
        data = [data]
        
    for event in data:
        event_type = event.get("eventType")
        if event_type in ["DeliveryOrderUpdate", "DeliveryOrderCreate", "DeliveryOrderStatusChanged"]:
            event_info = event.get("eventInfo", {})
            org_id = event.get("organizationId")
            
            o_data = event_info.get("order", event_info)
            order_id = o_data.get("id") or event_info.get("id")
            raw_status = o_data.get("status") or event_info.get("creationStatus")
            
            logger.info(f"WEBHOOK: [iiko_webhook] Event: {event_type} | Org: {org_id} | OrderID: {order_id} | Status: {raw_status}")
            
            if event_info:
                # Отправляем в фоновую задачу с новой сессией
                background_tasks.add_task(
                    run_sync_with_session,
                    iiko_sync_service.process_iiko_order,
                    event_info,
                    org_id
                )
                
    return {"status": "success"}

def run_sync_with_session(func, *args, **kwargs):
    """Хелпер для запуска асинхронной функции с новой сессией в фоновом потоке"""
    from app.core.database import engine
    import asyncio as sync_asyncio
    
    with Session(engine) as session:
        loop = sync_asyncio.new_event_loop()
        sync_asyncio.set_event_loop(loop)
        try:
            # Выполняем асинхронную функцию в новом цикле событий
            loop.run_until_complete(func(session, *args, **kwargs))
        except Exception as e:
            logger.error(f"Error in background task {func.__name__}: {e}", exc_info=True)
        finally:
            loop.close()


@router.post("/{order_id}/sync-iiko")
async def sync_order_from_iiko(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_edit")),
):
    """Принудительно обновить данные конкретного заказа из iiko"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if not order.iiko_order_id:
        raise HTTPException(status_code=400, detail="Order has no iiko ID")
        
    # Получаем organization_id через филиал или настройки
    org_id = order.branch.company.iiko_organization_id if order.branch and order.branch.company else None
    if not org_id:
        settings_db = session.exec(select(IikoSettings)).first()
        org_id = settings_db.organization_id if settings_db else None
        
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID not configured")
        
    success = await iiko_sync_service.sync_order_by_id(session, order.iiko_order_id, org_id)
    
    if success:
        return {"status": "success", "message": "Order data updated from iiko"}
    else:
        raise HTTPException(status_code=500, detail="Failed to sync order from iiko")


@router.post("/{order_id}/force-close")
async def force_close_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_edit")),
):
    """Принудительно закрыть заказ в базе данных и попытаться закрыть доставку в iiko"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    iiko_closed_status = "not_attempted"
    iiko_error_message = None

    # Попытка закрыть в iiko Cloud, если есть iiko_order_id
    if order.iiko_order_id:
        org_id = order.branch.company.iiko_organization_id if order.branch and order.branch.company else None
        if not org_id:
            settings_db = session.exec(select(IikoSettings)).first()
            org_id = settings_db.organization_id if settings_db else None

        if org_id:
            try:
                await iiko_service.close_delivery(org_id, order.iiko_order_id)
                iiko_closed_status = "success"
            except Exception as e:
                logger.warning(f"Failed to close order {order.id} ({order.iiko_order_id}) in iiko Cloud: {e}")
                iiko_closed_status = "failed"
                iiko_error_message = str(e)

    # Закрываем заказ в локальной БД
    order.status = OrderStatus.closed
    order.is_paid = True
    order.left_to_pay = Decimal("0.00")
    
    # Добавляем запись в историю статусов через единый сервис
    append_order_status_history(
        order=order,
        new_status=OrderStatus.closed,
        session=session,
        comment=f"Закрыт вручную администратором ({current_user.username or current_user.full_name or 'admin'})",
        user=current_user.full_name or current_user.username or "Admin"
    )

    session.add(order)
    session.commit()
    session.refresh(order)
    _invalidate_order_cache(order.id)

    return {
        "status": "success",
        "message": "Заказ успешно закрыт",
        "iiko_status": iiko_closed_status,
        "iiko_error": iiko_error_message,
        "order": {
            "id": order.id,
            "status": order.status,
            "is_paid": order.is_paid,
            "left_to_pay": float(order.left_to_pay)
        }
    }


@router.post("/sync")
def sync_recent_orders(
    background_tasks: BackgroundTasks, 
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_edit")),
):
    """
    Ручная синхронизация заказов из iiko (ревизии + последние 48 часов).
    """
    # Проверяем наличие настроек iiko в БД
    settings_db = session.exec(select(IikoSettings)).first()
    if not settings_db or not settings_db.api_login:
        raise HTTPException(status_code=400, detail="No iiko settings configured")
    
    async def run_sync():
        try:
            with Session(session.bind) as sync_session:
                # Синхронизация заказов (внутри логика по ревизиям и по датам -24h/+24h)
                logger.info("Starting manual order sync (Revision + 48h Window) via API")
                await iiko_sync_service.sync_orders(sync_session)
                logger.info("Manual order sync finished")
        except Exception as e:
            logger.error(f"Error in manual sync background task: {e}", exc_info=True)
    
    try:
        background_tasks.add_task(run_sync)
        return {"status": "accepted", "message": "Order synchronization started in background"}
    except Exception as e:
        logger.error(f"Failed to add manual sync task to background: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start synchronization: {str(e)}")


class OrderStatusUpdateRequest(BaseModel):
    status: str
    comment: Optional[str] = None


@router.post("/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: OrderStatusUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_edit")),
):
    """
    Изменение статуса заказа администратором с моментальной синхронизацией в iiko Cloud.
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Валидация статуса
    raw_status = request.status.strip().lower()
    matched_status = None
    for s in OrderStatus:
        if s.value.lower() == raw_status:
            matched_status = s
            break

    if not matched_status:
        raise HTTPException(status_code=400, detail=f"Недопустимый статус: {request.status}")

    old_status = order.status
    if old_status == matched_status:
        return {
            "status": "success",
            "message": f"Заказ уже находится в статусе '{matched_status.value}'",
            "order_status": matched_status.value,
            "iiko_synced": True
        }

    # Поиск organization_id для iiko
    org_id = None
    if order.branch and getattr(order.branch, "company", None) and order.branch.company.iiko_organization_id:
        org_id = str(order.branch.company.iiko_organization_id)
    if not org_id:
        settings_db = session.exec(select(IikoSettings)).first()
        org_id = str(settings_db.organization_id) if settings_db and settings_db.organization_id else None

    iiko_synced = False
    iiko_error = None

    # Если заказ выгружен в iiko (есть iiko_order_id)
    if order.iiko_order_id and org_id:
        iiko_uuid = str(order.iiko_order_id)
        try:
            if matched_status == OrderStatus.confirmed:
                logger.info(f"Confirming order {order.id} ({iiko_uuid}) in iiko Cloud")
                res = await iiko_service.confirm_delivery(organization_id=org_id, order_id=iiko_uuid)
                if isinstance(res, dict) and res.get("status") == "error":
                    iiko_error = res.get("message")
                else:
                    iiko_synced = True

            elif matched_status in [OrderStatus.cooking, OrderStatus.preparing, OrderStatus.assembling]:
                # В iiko если заказ был Unconfirmed, подтверждаем
                logger.info(f"Order {order.id} ({iiko_uuid}) cooking/preparation status started")
                try:
                    await iiko_service.confirm_delivery(organization_id=org_id, order_id=iiko_uuid)
                except Exception as ce:
                    logger.debug(f"Confirm on cooking in iiko returned: {ce}")
                iiko_synced = True

            elif matched_status in [OrderStatus.ready, OrderStatus.ready_for_pickup]:
                logger.info(f"Changing order {order.id} ({iiko_uuid}) to Waiting (ready) in iiko Cloud")
                res = await iiko_service.change_delivery_status(
                    organization_id=org_id,
                    order_id=iiko_uuid,
                    delivery_status="Waiting"
                )
                if isinstance(res, dict) and res.get("status") == "error":
                    iiko_error = res.get("message")
                else:
                    iiko_synced = True

            elif matched_status == OrderStatus.delivering:
                logger.info(f"Changing order {order.id} ({iiko_uuid}) to OnWay in iiko Cloud")
                res = await iiko_service.change_delivery_status(
                    organization_id=org_id,
                    order_id=iiko_uuid,
                    delivery_status="OnWay"
                )
                if isinstance(res, dict) and res.get("status") == "error":
                    iiko_error = res.get("message")
                else:
                    iiko_synced = True

            elif matched_status == OrderStatus.delivered:
                logger.info(f"Changing order {order.id} ({iiko_uuid}) to Delivered in iiko Cloud")
                res = await iiko_service.change_delivery_status(
                    organization_id=org_id,
                    order_id=iiko_uuid,
                    delivery_status="Delivered"
                )
                if isinstance(res, dict) and res.get("status") == "error":
                    iiko_error = res.get("message")
                else:
                    iiko_synced = True

            elif matched_status == OrderStatus.closed:
                logger.info(f"Closing delivery order {order.id} ({iiko_uuid}) in iiko Cloud")
                res = await iiko_service.close_delivery(organization_id=org_id, order_id=iiko_uuid)
                if isinstance(res, dict) and res.get("status") == "error":
                    iiko_error = res.get("message")
                else:
                    iiko_synced = True

            elif matched_status == OrderStatus.cancelled:
                logger.info(f"Cancelling order {order.id} ({iiko_uuid}) in iiko Cloud")
                res = await iiko_service.cancel_order(order_id=iiko_uuid, organization_id=org_id)
                if res is False:
                    iiko_error = "iiko вернул ошибку при отмене заказа"
                else:
                    iiko_synced = True

        except Exception as e:
            logger.error(f"Error syncing order status {matched_status.value} with iiko Cloud: {e}")
            iiko_error = str(e)
    else:
        # Заказ без iiko_order_id — локальное обновление
        iiko_synced = True

    # Обновляем заказ в локальной БД
    order.status = matched_status
    order.updated_at = datetime.now(timezone.utc)

    # Обновление связанных позиций кухни
    if matched_status in [OrderStatus.cooking, OrderStatus.preparing, OrderStatus.assembling]:
        items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        for item in items:
            if item.kitchen_status != "ready":
                item.kitchen_status = "cooking"
                if not item.kitchen_started_at:
                    item.kitchen_started_at = datetime.now(timezone.utc)
                session.add(item)
    elif matched_status in [OrderStatus.ready, OrderStatus.ready_for_pickup]:
        items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        for item in items:
            item.kitchen_status = "ready"
            if not item.kitchen_ready_at:
                item.kitchen_ready_at = datetime.now(timezone.utc)
            session.add(item)
    elif matched_status == OrderStatus.delivered:
        if not order.actual_time:
            order.actual_time = datetime.now(timezone.utc).replace(tzinfo=None)
    elif matched_status == OrderStatus.closed:
        order.is_paid = True
        order.left_to_pay = Decimal("0.00")
        if not order.actual_time:
            order.actual_time = datetime.now(timezone.utc).replace(tzinfo=None)

    # Добавление записи в историю жизненного цикла заказа
    user_label = current_user.full_name or current_user.username or "Admin"
    comment = request.comment or f"Статус изменен администратором ({user_label})"
    if iiko_synced and order.iiko_order_id:
        comment += " [iiko: синхронизировано]"
    elif iiko_error:
        comment += f" [iiko: ошибка: {iiko_error}]"

    append_order_status_history(
        order=order,
        new_status=matched_status,
        session=session,
        comment=comment,
        user=user_label
    )

    session.add(order)
    session.commit()
    session.refresh(order)
    _invalidate_order_cache(order.id)

    # WebSocket трансляция
    try:
        from app.api.chat import manager
        loop = asyncio.get_event_loop()
        ws_payload = {
            "type": "order_status_changed",
            "order_id": order.id,
            "order_number": order.external_number or str(order.id),
            "new_status": order.status.value,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        }
        if loop.is_running():
            loop.create_task(manager.broadcast(ws_payload))
        else:
            asyncio.run(manager.broadcast(ws_payload))
    except Exception as ws_err:
        logger.warning(f"Failed to broadcast WebSocket status update: {ws_err}")

    # Фоновый запуск роутера уведомлений VK/Telegram
    try:
        from app.services.vk_notification_router import vk_notification_router
        asyncio.create_task(vk_notification_router.route_event(
            event_type="order_status_update",
            payload={
                "order_id": order.id,
                "status": order.status.value,
                "old_status": old_status.value
            },
            db=session
        ))
    except Exception as notif_err:
        logger.warning(f"Failed to trigger notifications on status change: {notif_err}")

    return {
        "status": "success",
        "message": f"Статус заказа #{order.external_number or order.id} успешно изменен на '{matched_status.value}'",
        "order_status": order.status.value,
        "iiko_synced": iiko_synced,
        "iiko_error": iiko_error
    }


@router.post("/{order_id}/cooking-time")
async def update_order_cooking_time(
    order_id: int,
    minutes: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_edit")),
):
    """Обновление времени готовности заказа от кухни (в минутах)"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    old_cooking_time = order.cooking_time_minutes
    order.cooking_time_minutes = minutes
    order.cooking_time_updated_at = datetime.now(timezone.utc)
    session.add(order)
    session.commit()
    session.refresh(order)
    _invalidate_order_cache(order_id)
    
    logger.info(f"Updated cooking time for order {order_id} to {minutes} minutes by user {current_user.id}")
    
    # WebSocket трансляция изменений
    try:
        from app.api.chat import manager
        import asyncio
        loop = asyncio.get_event_loop()
        
        payload = {
            "type": "change_cooking_time",
            "order_id": order.id,
            "order_number": order.external_number or str(order.id),
            "cooking_time_minutes": order.cooking_time_minutes,
            "cooking_time_updated_at": order.cooking_time_updated_at.isoformat() if order.cooking_time_updated_at else None
        }
        
        if loop.is_running():
            loop.create_task(manager.broadcast(payload))
        else:
            asyncio.run(manager.broadcast(payload))
            
        # Уведомление назначенного курьера
        if order.courier_name:
            from app.models.employee import Employee
            from app.models.vk_bot import VkBotAccount
            from app.services.vk_bot_service import vk_bot_service
            from app.core.webpush_utils import send_web_push
            from app.models.admin_notification_settings import AdminNotificationSettings
            from app.models.push_subscription import PushSubscription
            from sqlalchemy import cast, String
            
            # Ищем сотрудника
            employee = session.exec(select(Employee).where(Employee.name == order.courier_name)).first()
            if employee:
                # 1. Личный WebSocket-сигнал курьеру
                c_user = session.exec(select(User).where(cast(User.iiko_id, String) == cast(employee.iiko_id, String))).first()
                if c_user:
                    ws_payload = {
                        "type": "change_cooking_time",
                        "order_id": order.id,
                        "order_number": order.external_number or str(order.id),
                        "cooking_time_minutes": order.cooking_time_minutes,
                        "cooking_time_updated_at": order.cooking_time_updated_at.isoformat() if order.cooking_time_updated_at else None
                    }
                    if loop.is_running():
                        loop.create_task(manager.send_personal_message(ws_payload, c_user.id))
                        
                    # 2. Web Push на телефон/браузер курьера
                    c_settings = session.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.user_id == c_user.id)).first()
                    if not c_settings or c_settings.change_cooking_time_push_enabled:
                        subscriptions = session.exec(select(PushSubscription).where(PushSubscription.user_id == c_user.id)).all()
                        if subscriptions:
                            global_settings = session.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.id == 1)).first()
                            if global_settings and global_settings.vapid_private_key:
                                title = "Время готовности установлено" if minutes > 0 else "Время готовности изменено"
                                body = f"Заказ #{order.external_number or order.id}. Время на кухне: {minutes} мин."
                                push_payload = json.dumps({
                                    "title": title,
                                    "body": body,
                                    "icon": "/favicon.ico",
                                    "url": "/pers/courier",
                                    "event_type": "change_cooking_time"
                                }, ensure_ascii=False)
                                
                                db_changed = False
                                for sub in subscriptions:
                                    sub_info = {
                                        "endpoint": sub.endpoint,
                                        "keys": {
                                            "p256dh": sub.p256dh,
                                            "auth": sub.auth
                                        }
                                    }
                                    res = send_web_push(sub_info, push_payload, global_settings.vapid_private_key)
                                    if res == "remove":
                                        session.delete(sub)
                                        db_changed = True
                                if db_changed:
                                    session.commit()
                                    
                # 3. Системные рассылки через шаблон (VK/Telegram/MAX/SMS)
                try:
                    from app.services.iiko_sync_service import iiko_sync_service
                    old_cook = int(old_cooking_time or 0)
                    new_cook = int(minutes or 0)
                    is_cooking_time_set = (old_cook <= 0 and new_cook > 0)
                    is_cooking_time_rechanged = (old_cook > 0 and new_cook > 0 and old_cook != new_cook)

                    # 3.1. Если время кухни задано впервые (>0 мин), досылаем order_new назначенному курьеру по цепочке
                    if is_cooking_time_set:
                        await iiko_sync_service.check_and_send_order_new_to_courier(order, session=session)

                    # 3.2. Отправка change_cooking_time (роутер проверит require_cooking_time_changed)
                    await iiko_sync_service.send_order_notification(
                        order, 
                        "change_cooking_time", 
                        session=session,
                        is_cooking_time_set=is_cooking_time_set,
                        is_cooking_time_rechanged=is_cooking_time_rechanged,
                        old_cooking_time=old_cook,
                        new_cooking_time=new_cook
                    )
                    
                    # Отправка выделенного персонального уведомления курьеру (Событие 2 или 3)
                    if c_user:
                        c_event = "courier_cooking_time_set" if (old_cooking_time is None or old_cooking_time == 0) else "courier_cooking_time_changed"
                        c_title = "Установлено время приготовления" if c_event == "courier_cooking_time_set" else "Изменено время приготовления"
                        c_body = f"Заказ #{order.external_number or order.id}. Время на кухне: {minutes} мин." if c_event == "courier_cooking_time_set" else f"Заказ #{order.external_number or order.id}. Новое время кухни: {minutes} мин. (было: {old_cooking_time} мин.)"
                        await iiko_sync_service.send_courier_notification(
                            session=session,
                            courier_user_id=c_user.id,
                            event_type=c_event,
                            title=c_title,
                            body=c_body,
                            order_id=order.id,
                            order_number=order.external_number or order.id,
                            url="/pers/courier",
                            extra_data={
                                "cooking_time_minutes": minutes,
                                "old_cooking_time": old_cooking_time,
                                "amount": float(order.total_with_discount or 0),
                                "address": order.delivery_address
                            },
                            order=order
                        )
                except Exception as notif_err:
                    logger.error(f"Failed to send change_cooking_time notification from update_order_cooking_time: {notif_err}")
    except Exception as ws_err:
        logger.error(f"Failed to broadcast cooking time change: {ws_err}")
        
    return {"status": "success", "message": "Cooking time updated successfully", "cooking_time_minutes": order.cooking_time_minutes}


from pydantic import BaseModel

class AssignCourierRequest(BaseModel):
    courier_iiko_id: str




@router.post("/{order_id}/courier")
async def assign_order_courier(
    order_id: int,
    payload: AssignCourierRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("orders_edit")),
):
    """
    Ручное назначение курьера на заказ в iiko и обновление локальной БД
    """
    from app.models.employee import Employee
    
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if not order.iiko_order_id:
        raise HTTPException(status_code=400, detail="Order has no iiko ID")
        
    org_id = order.branch.company.iiko_organization_id if order.branch and order.branch.company else None
    if not org_id:
        settings_db = session.exec(select(IikoSettings)).first()
        org_id = settings_db.organization_id if settings_db else None
        
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID not configured")
        
    employee = session.exec(
        select(Employee).where(Employee.iiko_id == payload.courier_iiko_id)
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Courier employee not found in database")
        
    try:
        logger.info(f"Assigning courier {employee.name} ({payload.courier_iiko_id}) to order {order.id} in iiko...")
        res = await iiko_service.assign_delivery_courier(
            organization_id=org_id,
            order_id=order.iiko_order_id,
            courier_id=payload.courier_iiko_id
        )
        
        if isinstance(res, dict) and res.get("status") == "error":
            raise HTTPException(status_code=400, detail=res.get("message", "iiko API error"))
            
        old_courier_name = order.courier_name
        is_reassigned = bool(old_courier_name and old_courier_name != "Не назначен" and old_courier_name != employee.name)
        order.courier_name = employee.name
        
        # При смене курьера обязательно сбрасываем статус подтверждения
        if is_reassigned or (old_courier_name != employee.name):
            order.courier_notification_status = None
            order.courier_accepted_at = None
            order.courier_accepted_source = None
            order.courier_read_at = None
            order.updated_at = datetime.now(timezone.utc)
            
        session.add(order)
        session.commit()
        session.refresh(order)

        # Рассылка WebSocket для мгновенного обновления интерфейса админки и курьеров
        try:
            from app.api.chat import manager
            import json
            now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
            ext_num = str(order.external_number or order.id)
            ws_order_changed = {
                "type": "order_changed",
                "order_id": order.id,
                "order_number": ext_num,
                "status": order.status,
                "customer_name": order.customer_name or "Гость",
                "order_type": order.order_type,
                "courier_name": order.courier_name,
                "courier_notification_status": order.courier_notification_status,
                "timestamp": now_ts
            }
            ws_courier_status = {
                "type": "courier_status_changed",
                "order_id": order.id,
                "order_num": ext_num,
                "courier_name": order.courier_name,
                "courier_notification_status": order.courier_notification_status,
                "status": "reassigned" if is_reassigned else "assigned",
                "timestamp": now_ts
            }
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(manager.broadcast(ws_order_changed))
                loop.create_task(manager.broadcast(ws_courier_status))
        except Exception as ws_err:
            logger.warning(f"Failed to broadcast websocket in assign_courier: {ws_err}")
        
        # Отправляем уведомление назначенному курьеру
        try:
            await iiko_sync_service.send_order_notification(order, "courier_assigned", session=session, is_reassigned=is_reassigned)
            if is_reassigned:
                logger.info(f"Order #{order.external_number or order.id} reassigned from '{old_courier_name}' to '{employee.name}'. Resending order_new to new courier.")
                await iiko_sync_service.send_order_notification(order, "order_new", session=session, is_reassigned=True)
            
            # 1. Выделенное персональное уведомление новому курьеру (Событие 1: Назначен заказ на доставку)
            new_c_user = iiko_sync_service.find_courier_user(session, employee.name, payload.courier_iiko_id)
            if new_c_user:
                await iiko_sync_service.send_courier_notification(
                    session=session,
                    courier_user_id=new_c_user.id,
                    event_type="courier_order_assigned",
                    title="Назначен заказ на доставку",
                    body=f"Вам назначен заказ #{order.external_number or order.id} | Сумма: {float(order.total_with_discount or 0):.0f} ₽ | Адрес: {order.delivery_address}",
                    order_id=order.id,
                    order_number=order.external_number or order.id,
                    url="/pers/courier",
                    extra_data={
                        "amount": float(order.total_with_discount or 0),
                        "address": order.delivery_address,
                        "customer_name": order.customer_name or "Гость",
                        "cooking_time_minutes": order.cooking_time_minutes
                    },
                    order=order
                )

            # 2. Выделенное уведомление старому курьеру при переназначении (Событие 9: Заказ убран из списка доставок выбранного курьера)
            if is_reassigned and old_courier_name:
                old_c_user = iiko_sync_service.find_courier_user(session, old_courier_name)
                if old_c_user:
                    await iiko_sync_service.send_courier_notification(
                        session=session,
                        courier_user_id=old_c_user.id,
                        event_type="courier_unassigned",
                        title="Заказ снят с ваших доставок",
                        body=f"Заказ #{order.external_number or order.id} убран из вашего списка доставок.",
                        order_id=order.id,
                        order_number=order.external_number or order.id,
                        url="/pers/courier",
                        extra_data={
                            "amount": float(order.total_with_discount or 0),
                            "address": order.delivery_address
                        },
                        order=order
                    )
        except Exception as notif_err:
            logger.error(f"Failed to send courier_assigned notification: {notif_err}")

        try:
            await iiko_sync_service.sync_order_by_id(session, order.iiko_order_id, org_id)
        except Exception as sync_err:
            logger.error(f"Failed to sync order after courier assignment: {sync_err}")
            
        return {"status": "success", "message": f"Courier {employee.name} assigned successfully", "courier_name": employee.name}
        
    except Exception as e:
        logger.error(f"Error assigning courier to order: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to assign courier in iiko: {e}")


