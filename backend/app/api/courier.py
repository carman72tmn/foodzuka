from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pydantic import BaseModel
import logging
import asyncio

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.iiko_service import iiko_service
from app.models.iiko_settings import IikoSettings
from app.models.payment_type import PaymentType
from app.models.order import Order, OrderStatus
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from app.services.iiko_sync_service import IikoSyncService
from app.core.datetime_utils import get_tz, get_local_now, get_day_boundaries
from app.services.order_status_history_service import append_order_status_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courier", tags=["Courier Operations"])
sync_service = IikoSyncService()

@router.get("/orders")
async def get_courier_orders(
    include_closed: bool = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    courier_filter: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение заказов из локальной БД. Только доставки."""
    
    try:
        query = select(Order).options(selectinload(Order.items)).where(Order.order_type == "Доставка")
        
        # Фильтрация по курьеру и ролям (если не суперюзер)
        if not current_user.is_superuser:
            user_permissions = [p.code for p in current_user.role.permissions] if current_user.role else []
            
            # Если у роли есть право видеть все доставки всех курьеров, мы не накладываем ограничений
            if "courier_view_assigned_all" in user_permissions:
                pass
            else:
                from sqlalchemy import or_
                conditions = []
                
                has_any_pref = any(p in user_permissions for p in ["courier_view_unassigned", "courier_view_assigned_self", "courier_view_assigned_all"])
                if "courier_view_assigned_self" in user_permissions or not has_any_pref:
                    courier_names = [current_user.full_name]
                    if current_user.employee and current_user.employee.name:
                        courier_names.append(current_user.employee.name)
                    conditions.append(Order.courier_name.in_(courier_names))
                
                # Доступ к неназначенным доставкам
                if "courier_view_unassigned" in user_permissions:
                    conditions.append((Order.courier_name == None) | (Order.courier_name == "") | (Order.courier_name == "Не назначен"))
                
                if conditions:
                    query = query.where(or_(*conditions))
                else:
                    query = query.where(Order.courier_name == "__impossible_name__")
        elif courier_filter:
            # Для админа - фильтр по конкретному курьеру
            query = query.where(Order.courier_name == courier_filter)
        
        # Фильтрация по статусам
        if include_closed:
            query = query.where(Order.status.in_([OrderStatus.closed, OrderStatus.cancelled, OrderStatus.delivered]))
        else:
            # Активные заказы: всё кроме завершенных
            query = query.where(Order.status.in_([
                OrderStatus.new, 
                OrderStatus.confirmed, 
                OrderStatus.preparing, 
                OrderStatus.cooking, 
                OrderStatus.ready, 
                OrderStatus.delivering,
                # OrderStatus.delivered, # Доставлен теперь в архиве, если включено
                OrderStatus.ready_for_pickup
            ]))
            
        # Фильтрация по датам (если переданы)
        tz_name = str(get_tz(db))
        logger.info(f"Fetching courier orders: include_closed={include_closed}, courier={courier_filter}, from={date_from}, to={date_to}, tz={tz_name}")
        
        has_date_filter = False
        if date_from:
            try:
                if len(date_from) == 10: # YYYY-MM-DD
                    start_utc, _ = get_day_boundaries(date_from, tz_name)
                else:
                    df = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                    start_utc = df.astimezone(timezone.utc).replace(tzinfo=None)
                query = query.where(Order.created_at >= start_utc)
                has_date_filter = True
                logger.info(f"Added date_from filter: >= {start_utc}")
            except Exception as e:
                logger.warning(f"Error parsing date_from {date_from}: {e}")
        
        if date_to:
            try:
                if len(date_to) == 10: # YYYY-MM-DD
                    _, end_utc = get_day_boundaries(date_to, tz_name)
                else:
                    dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                    end_utc = dt.astimezone(timezone.utc).replace(tzinfo=None)
                query = query.where(Order.created_at <= end_utc)
                has_date_filter = True
                logger.info(f"Added date_to filter: <= {end_utc}")
            except Exception as e:
                logger.warning(f"Error parsing date_to {date_to}: {e}")

        # [REFINED] Логика умолчаний для архива
        if include_closed and not has_date_filter:
            now_local = get_local_now(tz_name)
            # Если выбран курьер - показываем за последние 7 дней (по просьбе пользователя)
            if courier_filter or not current_user.is_superuser:
                df_local = (now_local - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
                logger.info(f"Default archive filter for courier {courier_filter or current_user.username} (7 days)")
            else:
                # Обычный архив - только за сегодня
                df_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
                logger.info(f"Default archive filter (today)")
                
            df_utc = df_local.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.where(Order.created_at >= df_utc)

        # Подсчет общего количества до пагинации
        count_query = select(func.count()).select_from(query.subquery())
        total_count = db.exec(count_query).one()

        query = query.order_by(Order.created_at.desc())
        
        # Пагинация
        query = query.offset((page - 1) * size).limit(size)
        
        orders_db = db.exec(query).all()
        
        result = []
        for o in orders_db:
            # Формируем плоскую структуру для фронтенда
            result.append({
                "id": str(o.iiko_order_id) if o.iiko_order_id else str(o.id),
                "local_id": o.id,
                "status": o.status,
                "number": o.external_number,
                "sum": float(o.total_amount),
                "total_with_discount": float(o.total_with_discount),
                "customer": {
                    "name": o.customer_name,
                    "phone": o.customer_phone
                },
                "address": {
                    "line1": o.delivery_address,
                    "city": o.city,
                    "street": o.street,
                    "house": o.house,
                    "flat": o.flat,
                    "entrance": o.entrance,
                    "floor": o.floor,
                    "doorphone": o.doorphone
                },
                "items": [
                    {
                        "name": item.get("name") or "Неизвестный товар",
                        "amount": item.get("amount") or item.get("quantity") or 1,
                        "price": float(item.get("price") or 0)
                    } for item in (o.order_items_details or [])
                ] if o.order_items_details else [
                    {
                        "name": item.product_name,
                        "amount": item.quantity,
                        "price": float(item.price)
                    } for item in o.items
                ],
                "comment": o.comment,
                "address_comment": o.address_comment,
                "additional_info": o.additional_info,
                "other_info": o.other_info,
                "courier_name": o.courier_name or "Не назначен",
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "expected_time": o.expected_time.isoformat() if o.expected_time else None,
                "actual_time": o.actual_time.isoformat() if o.actual_time else None,
                "delay_minutes": o.delay_minutes,
                "on_the_way_time": next((h.get("time") for h in reversed(o.status_history or []) if str(h.get("status", "")).lower() in ("delivering", "onway")), None),
                "ready_time": next((h.get("time") for h in reversed(o.status_history or []) if str(h.get("status", "")).lower() in ("ready", "readyfordelivery", "waiting")), None),
                "status_history": o.status_history or [],
                "status_changed_at": (o.status_history[-1].get("time") if (o.status_history and len(o.status_history) > 0 and isinstance(o.status_history[-1], dict)) else None) or (o.updated_at.isoformat() if getattr(o, "updated_at", None) else None) or (o.created_at.isoformat() if o.created_at else None),
                "order_type": o.order_type,
                "payment_method": o.payment_method,
                "is_paid": o.is_paid,
                "left_to_pay": float(o.left_to_pay),
                "total_amount": float(o.total_amount),
                "total_with_discount": float(o.total_with_discount),
                "payments_details": o.payments_details,
                "is_asap": o.is_asap,
                "is_on_time": o.is_on_time,
                "delivery_zone": o.delivery_zone,
                "iiko_creation_time": o.iiko_creation_time.isoformat() if o.iiko_creation_time else None,
                "customer_info_details": o.customer_info_details,
                "change_indicators": o.change_indicators,
                "cooking_time_minutes": o.cooking_time_minutes,
                "cooking_time_updated_at": o.cooking_time_updated_at.isoformat() if o.cooking_time_updated_at else None,
                "courier_notification_status": o.courier_notification_status,
                "courier_accepted_at": o.courier_accepted_at.isoformat() if o.courier_accepted_at else None,
                "courier_accepted_source": o.courier_accepted_source,
                "courier_read_at": o.courier_read_at.isoformat() if o.courier_read_at else None,
                "courier_notification_channel": o.courier_notification_channel,
                "courier_last_message_text": o.courier_last_message_text,
                "number": o.external_number or str(o.id)
            })
            
        return {
            "status": "success", 
            "data": result,
            "pagination": {
                "total": total_count,
                "page": page,
                "size": size,
                "pages": (total_count + size - 1) // size
            }
        }
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dates")
async def get_courier_dates(
    courier_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка уникальных дат, в которые у курьера были доставки"""
    if not current_user.is_superuser and current_user.full_name != courier_name:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
        
    try:
        # Получаем уникальные даты из created_at
        # В PostgreSQL это можно сделать через date_trunc или cast к date
        query = select(func.distinct(func.date(Order.created_at))).where(
            Order.courier_name == courier_name,
            Order.order_type == "Доставка"
        ).order_by(func.date(Order.created_at).desc()).limit(30)
        
        dates = db.exec(query).all()
        return {"status": "success", "data": [d.isoformat() for d in dates if d]}
    except Exception as e:
        logger.error(f"Error fetching courier dates: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/sync")
async def manual_sync_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Принудительная синхронизация заказов из iiko"""
    settings = db.exec(select(IikoSettings)).first()
    if not settings:
        return {"status": "error", "message": "Настройки iiko не найдены"}
        
    try:
        # 1. Запускаем быструю синхронизацию по ревизиям (catch-up вебхуков)
        # [OPTIMIZED] Используем только быструю синхронизацию (fast_only=True)
        # Удаляем sync_courier_deliveries, так как OLAP-отчеты iiko слишком тяжелые для RMS
        # и вызывают зависания при частом обращении.
        # Все необходимые данные по курьерам теперь берутся из iikoCloud API (sync_orders).
        await sync_service.sync_orders(db, fast_only=True)
        
        logger.info("Manual courier sync completed (fast only)")
        return {"status": "success", "message": "Синхронизация завершена"}
    except Exception as e:
        logger.error(f"Manual sync error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/shifts")
async def get_active_shifts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Просмотр активных кассовых смен (только для Супер Админа)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
        
    settings = db.exec(select(IikoSettings)).first()
    date_from = datetime.now() - timedelta(days=2)
    date_to = datetime.now() + timedelta(days=1)
    
    try:
        shifts = await iiko_service.get_cash_shifts(
            organization_id=settings.organization_id,
            date_from=date_from,
            date_to=date_to,
            status="OPEN"
        )
        
        if isinstance(shifts, dict) and shifts.get("status") == "error":
            error_code = shifts.get("error")
            if error_code in ["IIKO_RIGHTS_ERROR", "UNAUTHORIZED"]:
                logger.warning(f"Iiko Shifts Access Denied for user {current_user.id}: {shifts.get('message')}")
                return {"status": "success", "data": []}
            raise HTTPException(status_code=400, detail=shifts.get("message"))
            
        return {"status": "success", "data": shifts}
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "403" in err_str or "RIGHTS" in err_str.upper():
            logger.warning(f"Iiko Shifts Access Denied (Exception): {e}")
            return {"status": "success", "data": []}
        logger.error(f"Error fetching shifts: {e}")
        return {"status": "success", "data": []}

def _get_local_active_couriers_fallback(db: Session) -> list:
    """Локальный фоллбэк: курьеры с открытыми сменами в нашей БД"""
    from app.models.employee import Shift, Employee
    open_shifts = db.exec(
        select(Shift)
        .join(Employee)
        .where(Shift.status == "OPEN", Employee.is_courier == True, Employee.status == "Active")
    ).all()
    
    seen = set()
    data = []
    for s in open_shifts:
        if s.employee and s.employee.iiko_id not in seen:
            seen.add(s.employee.iiko_id)
            data.append({
                "id": s.employee.iiko_id,
                "name": s.employee.name,
                "latitude": None,
                "longitude": None,
                "is_fallback": True
            })
    return data


@router.get("/active-couriers")
async def get_active_couriers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Просмотр активных курьеров (только для Супер Админа)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
        
    from app.models.employee import Employee
    
    settings = db.exec(select(IikoSettings)).first()
    organization_id = settings.organization_id if settings else None
    
    # Загружаем активных курьеров из нашей БД
    db_couriers = db.exec(
        select(Employee).where(Employee.is_courier == True, Employee.status == "Active")
    ).all()
    courier_by_iiko_id = {c.iiko_id: c for c in db_couriers}
    
    if not organization_id:
        logger.warning("No iiko settings or organization ID. Using local active shifts fallback.")
        return {"status": "success", "data": _get_local_active_couriers_fallback(db)}
        
    try:
        active_locations = await iiko_service.get_active_couriers(
            organization_id=organization_id
        )
        
        if isinstance(active_locations, dict) and active_locations.get("status") == "error":
            logger.warning(f"Iiko active couriers error: {active_locations}. Using local active shifts fallback.")
            return {"status": "success", "data": _get_local_active_couriers_fallback(db)}
            
        data = []
        if active_locations:
            for loc in active_locations:
                c_id = loc.get("id")
                emp = courier_by_iiko_id.get(c_id)
                if emp:
                    data.append({
                        "id": emp.iiko_id,
                        "name": emp.name,
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude")
                    })
                else:
                    logger.warning(f"Active courier ID {c_id} from iiko not found/active in local DB, skipping.")
        
        return {"status": "success", "data": data}
        
    except Exception as e:
        logger.error(f"Error fetching active couriers from iiko: {e}. Using local active shifts fallback.")
        return {"status": "success", "data": _get_local_active_couriers_fallback(db)}


class CourierShiftActionRequest(BaseModel):
    employee_iiko_id: Optional[str] = None
    terminal_group_id: Optional[str] = None


@router.get("/my-shift-status")
async def get_my_shift_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Персональный статус смены курьера в iiko Cloud"""
    from app.models.employee import Employee
    from app.models.iiko_settings import IikoSettings
    
    settings = db.exec(select(IikoSettings)).first()
    org_id = settings.organization_id if settings else None

    # Ищем сотрудника
    emp = None
    emp_id = getattr(current_user, "employee_id", None)
    if emp_id:
        emp = db.get(Employee, emp_id)
    if not emp and getattr(current_user, "employee", None):
        emp = current_user.employee
    if not emp and getattr(current_user, "iiko_id", None):
        emp = db.exec(select(Employee).where(Employee.iiko_id == str(current_user.iiko_id))).first()
    if not emp and getattr(current_user, "full_name", None):
        emp = db.exec(select(Employee).where(Employee.name == current_user.full_name)).first()
    if not emp and getattr(current_user, "phone", None):
        emp = db.exec(select(Employee).where(Employee.phone == current_user.phone)).first()

    if not emp or not emp.iiko_id:
        # Проверяем, может быть у самого юзера есть iiko_id
        iiko_id = getattr(current_user, "iiko_id", None)
        if not iiko_id:
            return {
                "status": "success",
                "is_courier": False,
                "is_shift_open": False,
                "message": "Сотрудник не привязан к iiko"
            }
        courier_iiko_id = iiko_id
        courier_name = current_user.full_name or "Курьер"
    else:
        courier_iiko_id = emp.iiko_id
        courier_name = emp.name

    default_terminal_group_id = (
        (settings.terminal_group_id if settings else None) 
        or "f4b59175-38e0-43ae-bbc6-1f37251c33bf"
    )

    try:
        shifts = await iiko_service.get_courier_shifts(courier_iiko_id)
        is_open = bool(shifts and len(shifts) > 0)
        active_tg = shifts[0] if is_open else default_terminal_group_id
        
        return {
            "status": "success",
            "is_courier": True,
            "is_shift_open": is_open,
            "courier_name": courier_name,
            "courier_iiko_id": courier_iiko_id,
            "terminal_group_id": active_tg,
            "terminal_groups_open": shifts
        }
    except Exception as e:
        logger.error(f"Error checking my shift status: {e}")
        return {
            "status": "success",
            "is_courier": True,
            "is_shift_open": False,
            "courier_name": courier_name,
            "courier_iiko_id": courier_iiko_id,
            "terminal_group_id": default_terminal_group_id,
            "terminal_groups_open": [],
            "error": str(e)
        }


@router.post("/open-shift")
async def open_my_shift(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Персональное открытие смены курьера в iiko Front/Office"""
    from app.models.employee import Employee, Shift
    from app.models.iiko_settings import IikoSettings
    
    settings = db.exec(select(IikoSettings)).first()
    if not settings or not settings.organization_id:
        raise HTTPException(status_code=400, detail="Настройки iiko не сконфигурированы")

    emp = None
    if getattr(current_user, "employee", None):
        emp = current_user.employee
    if not emp and getattr(current_user, "iiko_id", None):
        emp = db.exec(select(Employee).where(Employee.iiko_id == str(current_user.iiko_id))).first()
    if not emp and getattr(current_user, "full_name", None):
        emp = db.exec(select(Employee).where(Employee.name == current_user.full_name)).first()

    courier_iiko_id = emp.iiko_id if (emp and emp.iiko_id) else getattr(current_user, "iiko_id", None)
    if not courier_iiko_id:
        raise HTTPException(status_code=400, detail="Ваш профиль не связан с сотрудником iiko")

    terminal_group_id = settings.terminal_group_id or "f4b59175-38e0-43ae-bbc6-1f37251c33bf"

    from app.models.role import Role
    courier_role = db.exec(select(Role).where(Role.code == "CUR")).first()
    courier_role_iiko_id = str(courier_role.iiko_id) if (courier_role and courier_role.iiko_id) else "112da4c3-5323-45a7-a033-bf5265d66608"

    try:
        res = await iiko_service.clockin_courier_shift(
            organization_id=settings.organization_id,
            terminal_group_id=terminal_group_id,
            employee_id=courier_iiko_id,
            role_id=courier_role_iiko_id
        )
        logger.info(f"Courier {current_user.full_name} ({courier_iiko_id}) clocked in iiko: {res}")

        if isinstance(res, dict) and res.get("status") == "error":
            raise HTTPException(status_code=400, detail=f"Ошибка iiko: {res.get('message', 'Не удалось открыть смену')}")

        # Проверяем статус асинхронной команды через correlationId
        corr_id = res.get("correlationId") if isinstance(res, dict) else None
        if corr_id:
            for _ in range(3):
                await asyncio.sleep(1)
                try:
                    c_status = await iiko_service.get_command_status(settings.organization_id, corr_id)
                    if isinstance(c_status, dict):
                        st = str(c_status.get("state", "")).upper()
                        if st in ("ERROR", "CANCELLED", "FAILED"):
                            err_msg = c_status.get("error") or c_status.get("message") or "Терминал iiko отклонил открытие смены"
                            raise HTTPException(status_code=400, detail=f"Ошибка терминала iiko: {err_msg}")
                        elif st == "SUCCESS":
                            break
                except HTTPException:
                    raise
                except Exception as ce:
                    logger.debug(f"Command status check failed: {ce}")

        # Фиксируем в локальной таблице смен
        if emp:
            existing_shift = db.exec(
                select(Shift).where(Shift.employee_id == emp.id, Shift.status == "OPEN")
            ).first()
            if not existing_shift:
                import time
                shift_iiko_id = (res.get("id") or res.get("sessionId") or res.get("correlationId")) if isinstance(res, dict) else None
                if not shift_iiko_id:
                    shift_iiko_id = f"shift-{emp.id}-{int(time.time())}"
                new_shift = Shift(
                    iiko_id=str(shift_iiko_id),
                    employee_id=emp.id,
                    status="OPEN",
                    date_open=datetime.now(timezone.utc)
                )
                db.add(new_shift)
                db.commit()
                db.refresh(new_shift)
                try:
                    from app.services.iiko_sync_service import iiko_sync_service
                    asyncio.create_task(iiko_sync_service._send_shift_vk_notification(new_shift, emp, "shift_open"))
                except Exception as ne:
                    logger.warning(f"Error triggering shift_open notification: {ne}")

        return {
            "status": "success",
            "message": "Смена в iiko успешно открыта!",
            "is_shift_open": True,
            "result": res
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error opening shift in iiko: {e}")
        raise HTTPException(status_code=500, detail=f"Не удалось открыть смену в iiko: {e}")


# Стоп-слова для исключения системных и служебных аккаунтов из списка курьеров
SYSTEM_COURIER_STOP_WORDS = [
    "администратор", "пользователь", "системный", "системная", 
    "учетная", "юзер", "user", "admin", "админ", "iiko"
]

def is_system_courier(name: Optional[str]) -> bool:
    if not name:
        return False
    name_lower = name.lower()
    return any(stop_word in name_lower for stop_word in SYSTEM_COURIER_STOP_WORDS)


@router.get("/all-couriers-shifts")
async def get_all_couriers_with_shifts(
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Список ВСЕХ курьеров (активных и неактивных) со статусами смен iiko (для админов, с кэшированием)"""
    from app.models.employee import Employee, HiddenCourier
    from app.models.iiko_settings import IikoSettings
    
    settings = db.exec(select(IikoSettings)).first()
    org_id = settings.organization_id if settings else None

    # Получаем локальных курьеров, исключая системные аккаунты
    db_couriers = db.exec(
        select(Employee).where(
            (Employee.is_courier == True) | 
            (func.lower(Employee.role).contains("курьер")) |
            (func.lower(Employee.name).contains("курьер"))
        )
    ).all()
    courier_by_iiko_id = {c.iiko_id: c for c in db_couriers if c.iiko_id}

    # Получаем множество скрытых курьеров из базы данных
    hidden_ids = {h.courier_iiko_id for h in db.exec(select(HiddenCourier)).all()}

    # Запрашиваем официальных курьеров из iiko
    iiko_couriers = []
    if org_id:
        try:
            iiko_couriers = await iiko_service.get_couriers(org_id)
        except Exception as e:
            logger.warning(f"Failed to fetch couriers from iiko: {e}")

    # Запрашиваем активные локации из iiko
    active_loc_ids = set()
    if org_id:
        try:
            active_locs = await iiko_service.get_active_couriers(org_id)
            for loc in active_locs:
                if loc.get("id"):
                    active_loc_ids.add(loc.get("id"))
        except Exception as e:
            logger.warning(f"Failed to fetch active locations: {e}")

    couriers_map = {}

    # 1. Заполняем курьеров из iiko
    for ic in iiko_couriers:
        c_id = ic.get("id")
        if not c_id:
            continue
        c_name = ic.get("displayName") or ic.get("name") or "Курьер"
        c_phone = ic.get("phone")
        emp = courier_by_iiko_id.get(c_id)
        full_name = emp.name if (emp and emp.name) else c_name

        # Исключаем системные учетные записи
        if is_system_courier(full_name) or is_system_courier(c_name) or is_system_courier(ic.get("name")):
            continue

        couriers_map[c_id] = {
            "id": emp.id if emp else None,
            "iiko_id": c_id,
            "name": full_name,
            "phone": emp.phone if (emp and emp.phone) else c_phone,
            "code": ic.get("code"),
            "is_shift_open": False,
            "terminal_group_id": None,
            "is_online": c_id in active_loc_ids,
            "status": emp.status if emp else "Active",
            "is_hidden": c_id in hidden_ids
        }

    # 2. Добавляем локальных курьеров, которых нет в ответе iiko
    for emp in db_couriers:
        c_id = emp.iiko_id or f"local_{emp.id}"
        if is_system_courier(emp.name) or is_system_courier(emp.role):
            continue
        if c_id not in couriers_map:
            couriers_map[c_id] = {
                "id": emp.id,
                "iiko_id": emp.iiko_id,
                "name": emp.name,
                "phone": emp.phone,
                "code": emp.code,
                "is_shift_open": False,
                "terminal_group_id": None,
                "is_online": False,
                "status": emp.status or "Active",
                "is_hidden": (emp.iiko_id in hidden_ids) if emp.iiko_id else False
            }

    # 3. Для курьеров запрашиваем статус открытой смены в iiko (параллельно и с кэшем)
    default_tg = settings.terminal_group_id or "f4b59175-38e0-43ae-bbc6-1f37251c33bf" if settings else None

    async def _fetch_courier_shift(data: dict):
        c_iiko_id = data.get("iiko_id")
        if not c_iiko_id or str(c_iiko_id).startswith("local_"):
            return
        # Для скрытых курьеров без активности не тратим квоту API, если не запрошено принудительно
        if data.get("is_hidden") and not data.get("is_online") and not force:
            return
        try:
            tg_ids = await iiko_service.get_courier_shifts(c_iiko_id, organization_id=org_id, force=force)
            if tg_ids and len(tg_ids) > 0:
                data["is_shift_open"] = True
                data["terminal_group_id"] = tg_ids[0]
            elif data.get("is_online"):
                data["is_shift_open"] = True
                data["terminal_group_id"] = default_tg
        except Exception as e:
            logger.debug(f"Error checking shifts for {c_iiko_id}: {e}")

    await asyncio.gather(*[_fetch_courier_shift(data) for data in couriers_map.values()])

    result_list = list(couriers_map.values())
    result_list.sort(key=lambda x: (x.get("is_hidden", False), not x["is_shift_open"], x["name"] or ""))

    return {"status": "success", "data": result_list}


@router.post("/admin/open-shift")
async def admin_open_courier_shift(
    payload: CourierShiftActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Открыть смену выбранного курьера в iiko (для админов)"""
    from app.models.iiko_settings import IikoSettings
    from app.models.employee import Employee, Shift
    
    if not current_user.is_superuser:
        user_perms = [p.code for p in current_user.role.permissions] if current_user.role else []
        if "couriers_manage" not in user_perms and "courier_view" not in user_perms and not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="Доступ запрещен")

    if not payload.employee_iiko_id:
        raise HTTPException(status_code=400, detail="Не указан employee_iiko_id курьера")

    settings = db.exec(select(IikoSettings)).first()
    if not settings or not settings.organization_id:
        raise HTTPException(status_code=400, detail="Настройки iiko не сконфигурированы")

    tg_id = payload.terminal_group_id or settings.terminal_group_id or "f4b59175-38e0-43ae-bbc6-1f37251c33bf"

    from app.models.role import Role
    courier_role = db.exec(select(Role).where(Role.code == "CUR")).first()
    courier_role_iiko_id = str(courier_role.iiko_id) if (courier_role and courier_role.iiko_id) else "112da4c3-5323-45a7-a033-bf5265d66608"

    try:
        res = await iiko_service.clockin_courier_shift(
            organization_id=settings.organization_id,
            terminal_group_id=tg_id,
            employee_id=payload.employee_iiko_id,
            role_id=courier_role_iiko_id
        )
        logger.info(f"Admin {current_user.username} opened shift for courier {payload.employee_iiko_id}: {res}")

        if isinstance(res, dict) and res.get("status") == "error":
            raise HTTPException(status_code=400, detail=f"Ошибка iiko: {res.get('message', 'Не удалось открыть смену')}")

        # Проверяем статус асинхронной команды через correlationId
        corr_id = res.get("correlationId") if isinstance(res, dict) else None
        if corr_id:
            for _ in range(3):
                await asyncio.sleep(1)
                try:
                    c_status = await iiko_service.get_command_status(settings.organization_id, corr_id)
                    if isinstance(c_status, dict):
                        st = str(c_status.get("state", "")).upper()
                        if st in ("ERROR", "CANCELLED", "FAILED"):
                            err_msg = c_status.get("error") or c_status.get("message") or "Терминал iiko отклонил открытие смены"
                            raise HTTPException(status_code=400, detail=f"Ошибка терминала iiko: {err_msg}")
                        elif st == "SUCCESS":
                            break
                except HTTPException:
                    raise
                except Exception as ce:
                    logger.debug(f"Command status check failed: {ce}")

        emp = db.exec(select(Employee).where(Employee.iiko_id == payload.employee_iiko_id)).first()
        if emp:
            import time
            shift_iiko_id = (res.get("id") or res.get("sessionId") or res.get("correlationId")) if isinstance(res, dict) else None
            if not shift_iiko_id:
                shift_iiko_id = f"shift-{emp.id}-{int(time.time())}"
            new_shift = Shift(
                iiko_id=str(shift_iiko_id),
                employee_id=emp.id,
                status="OPEN",
                date_open=datetime.now(timezone.utc)
            )
            db.add(new_shift)
            db.commit()
            db.refresh(new_shift)
            try:
                from app.services.iiko_sync_service import iiko_sync_service
                asyncio.create_task(iiko_sync_service._send_shift_vk_notification(new_shift, emp, "shift_open"))
            except Exception as ne:
                logger.warning(f"Error triggering shift_open notification: {ne}")

        return {"status": "success", "message": "Смена курьера открыта в iiko", "result": res}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error opening courier shift by admin: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка открытия смены в iiko: {e}")


@router.post("/admin/close-shift")
async def admin_close_courier_shift(
    payload: CourierShiftActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Закрыть смену выбранного курьера в iiko (для админов)"""
    from app.models.iiko_settings import IikoSettings
    from app.models.employee import Employee, Shift
    
    if not current_user.is_superuser:
        user_perms = [p.code for p in current_user.role.permissions] if current_user.role else []
        if "couriers_manage" not in user_perms and "courier_view" not in user_perms and not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="Доступ запрещен")

    if not payload.employee_iiko_id:
        raise HTTPException(status_code=400, detail="Не указан employee_iiko_id курьера")

    settings = db.exec(select(IikoSettings)).first()
    if not settings or not settings.organization_id:
        raise HTTPException(status_code=400, detail="Настройки iiko не сконфигурированы")

    # Ищем открытые смены курьера в терминальных группах
    tg_id = payload.terminal_group_id
    if not tg_id:
        try:
            tg_ids = await iiko_service.get_courier_shifts(payload.employee_iiko_id, organization_id=settings.organization_id)
            if tg_ids:
                tg_id = tg_ids[0]
        except Exception:
            pass
    if not tg_id:
        tg_id = settings.terminal_group_id or "f4b59175-38e0-43ae-bbc6-1f37251c33bf"

    try:
        res = await iiko_service.clockout_courier_shift(
            organization_id=settings.organization_id,
            terminal_group_id=tg_id,
            employee_id=payload.employee_iiko_id
        )
        logger.info(f"Admin {current_user.username} closed shift for courier {payload.employee_iiko_id}: {res}")

        emp = db.exec(select(Employee).where(Employee.iiko_id == payload.employee_iiko_id)).first()
        if emp:
            open_shifts = db.exec(
                select(Shift).where(Shift.employee_id == emp.id, Shift.status == "OPEN")
            ).all()
            for s in open_shifts:
                s.status = "CLOSED"
                s.closed_at = datetime.now(timezone.utc)
                s.date_close = datetime.now(timezone.utc)
                db.add(s)
                try:
                    from app.services.iiko_sync_service import iiko_sync_service
                    asyncio.create_task(iiko_sync_service._send_shift_vk_notification(s, emp, "shift_close"))
                except Exception as ne:
                    logger.warning(f"Error triggering shift_close notification: {ne}")
            db.commit()

        return {"status": "success", "message": "Смена курьера закрыта в iiko", "result": res}
    except Exception as e:
        logger.error(f"Error closing courier shift by admin: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка закрытия смены в iiko: {e}")


@router.post("/orders/{order_id}/accept-order")
async def accept_order_by_courier(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Подтверждение принятия заказа курьером (кнопка 'Принял заказ' в карточке доставки)"""
    from app.models.vk_bot import CourierOrderNotification
    import asyncio
    
    order = _find_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    now = datetime.now(timezone.utc)
    order.courier_notification_status = "accepted"
    order.courier_accepted_at = now
    order.courier_accepted_source = "button"
    order.courier_last_message_text = "Принял заказ в приложении"
    order.updated_at = now
    db.add(order)

    # Обновляем детальный лог курьерских уведомлений
    notif = db.exec(
        select(CourierOrderNotification)
        .where(CourierOrderNotification.order_id == order.id)
        .order_by(CourierOrderNotification.id.desc())
    ).first()
    if notif:
        notif.status = "accepted"
        notif.accepted_at = now
        notif.reply_text = "Принял заказ (кнопка в карточке)"
        notif.updated_at = now
        db.add(notif)
    else:
        new_notif = CourierOrderNotification(
            order_id=order.id,
            courier_name=order.courier_name or current_user.full_name,
            channel="app",
            status="accepted",
            accepted_at=now,
            reply_text="Принял заказ (кнопка в карточке)"
        )
        db.add(new_notif)

    db.commit()
    db.refresh(order)

    # WebSocket оповещение для моментального обновления зеленого кружка в админке
    try:
        from app.api.chat import manager
        payload_ws = {
            "type": "courier_status_changed",
            "order_id": order.id,
            "order_num": str(order.external_number or order.id),
            "courier_name": order.courier_name,
            "courier_notification_status": "accepted",
            "courier_last_message_text": order.courier_last_message_text,
            "status": "accepted",
            "timestamp": int(now.timestamp() * 1000)
        }
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(manager.broadcast(payload_ws))
    except Exception as ws_err:
        logger.warning(f"Failed to broadcast websocket on accept_order: {ws_err}")

    return {
        "status": "success",
        "message": "Заказ успешно принят курьером",
        "order_id": order.id,
        "courier_notification_status": "accepted",
        "accepted_at": order.courier_accepted_at.isoformat() if order.courier_accepted_at else None
    }


class CourierHideActionRequest(BaseModel):
    employee_iiko_id: str


@router.post("/admin/hide-courier")
async def admin_hide_courier(
    payload: CourierHideActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Скрыть курьера из общего списка (перенести во вкладку 'Скрытые')"""
    from app.models.employee import HiddenCourier, Employee
    if not current_user.is_superuser:
        user_perms = [p.code for p in current_user.role.permissions] if current_user.role else []
        if "couriers_manage" not in user_perms and "courier_view" not in user_perms and not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="Доступ запрещен")

    if not payload.employee_iiko_id:
        raise HTTPException(status_code=400, detail="Не указан employee_iiko_id")

    existing = db.get(HiddenCourier, payload.employee_iiko_id)
    if not existing:
        emp = db.exec(select(Employee).where(Employee.iiko_id == payload.employee_iiko_id)).first()
        hidden_rec = HiddenCourier(
            courier_iiko_id=payload.employee_iiko_id,
            courier_name=emp.name if emp else None,
            hidden_at=datetime.now(timezone.utc)
        )
        db.add(hidden_rec)
        db.commit()

    return {"status": "success", "message": "Курьер успешно скрыт"}


@router.post("/admin/unhide-courier")
async def admin_unhide_courier(
    payload: CourierHideActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Восстановить скрытого курьера (вернуть в общий список)"""
    from app.models.employee import HiddenCourier
    if not current_user.is_superuser:
        user_perms = [p.code for p in current_user.role.permissions] if current_user.role else []
        if "couriers_manage" not in user_perms and "courier_view" not in user_perms and not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="Доступ запрещен")

    if not payload.employee_iiko_id:
        raise HTTPException(status_code=400, detail="Не указан employee_iiko_id")

    existing = db.get(HiddenCourier, payload.employee_iiko_id)
    if existing:
        db.delete(existing)
        db.commit()

    return {"status": "success", "message": "Курьер успешно восстановлен в общий список"}


@router.get("/admin/courier-report")
async def get_courier_delivery_report(
    courier_name: Optional[str] = Query(None, description="Имя курьера"),
    courier_iiko_id: Optional[str] = Query(None, description="iiko ID курьера"),
    date_from: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD или ISO)"),
    date_to: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD или ISO)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Детализированный отчет по доставкам курьера по дням, зонам, способам оплаты и опозданиям"""
    if not current_user.is_superuser:
        user_perms = [p.code for p in current_user.role.permissions] if current_user.role else []
        if "courier_view" not in user_perms and "courier_reports_view" not in user_perms and not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="Доступ запрещен")

    from app.models.order import Order
    from app.models.employee import Employee
    from app.models.iiko_settings import IikoSettings
    import zoneinfo

    # 1. Определяем целевое имя курьера
    target_name = courier_name
    if not target_name and courier_iiko_id:
        emp = db.exec(select(Employee).where(Employee.iiko_id == courier_iiko_id)).first()
        if emp:
            target_name = emp.name

    if not target_name:
        raise HTTPException(status_code=400, detail="Необходимо указать courier_name или courier_iiko_id")

    # 2. Часовой пояс
    settings = db.exec(select(IikoSettings)).first()
    tz_name = (settings.timezone_name if settings and settings.timezone_name else None) or "Asia/Yekaterinburg"
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = timezone(timedelta(hours=5))

    # 3. Фильтрация
    filters = [
        Order.order_type == "Доставка",
        (Order.courier_name == target_name) | (Order.courier_name.ilike(f"%{target_name}%"))
    ]

    if date_from:
        try:
            if len(date_from) == 10:
                df = datetime.fromisoformat(f"{date_from}T00:00:00").replace(tzinfo=tz).astimezone(timezone.utc)
            else:
                df = datetime.fromisoformat(date_from).astimezone(timezone.utc)
            filters.append(Order.created_at >= df)
        except Exception as e:
            logger.warning(f"Error parsing date_from {date_from}: {e}")

    if date_to:
        try:
            if len(date_to) == 10:
                dt = datetime.fromisoformat(f"{date_to}T23:59:59").replace(tzinfo=tz).astimezone(timezone.utc)
            else:
                dt = datetime.fromisoformat(date_to).astimezone(timezone.utc)
            filters.append(Order.created_at <= dt)
        except Exception as e:
            logger.warning(f"Error parsing date_to {date_to}: {e}")

    orders = db.exec(select(Order).where(*filters).order_by(Order.created_at.desc())).all()

    # 4. Агрегация по дням
    days_map = {}
    summary_zones = {}
    summary_payments = {}
    total_orders = 0
    total_revenue = 0.0
    total_late = 0

    WEEKDAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    for ord_item in orders:
        total_orders += 1
        amount = float(ord_item.total_with_discount or ord_item.total_paid or 0.0)
        total_revenue += amount

        created_utc = ord_item.created_at or datetime.now(timezone.utc)
        if created_utc.tzinfo is None:
            created_utc = created_utc.replace(tzinfo=timezone.utc)
        local_dt = created_utc.astimezone(tz)
        day_key = local_dt.strftime("%Y-%m-%d")

        # Зона доставки
        zone_raw = ord_item.delivery_zone
        zone_name = zone_raw.strip() if zone_raw else "Без зоны"

        # Способ оплаты
        pay_raw = ord_item.payment_method or "Не указан"
        pay_name = pay_raw
        pay_raw_lower = pay_raw.lower()
        if "нал" in pay_raw_lower:
            pay_name = "Наличные"
        elif "карт" in pay_raw_lower or "pos" in pay_raw_lower or "терминал" in pay_raw_lower:
            pay_name = "Картой курьеру"
        elif "сбп" in pay_raw_lower or "sbp" in pay_raw_lower:
            pay_name = "СБП (QR)"
        elif "сайт" in pay_raw_lower or "онлайн" in pay_raw_lower:
            pay_name = "Оплата на сайте"

        # Опоздание
        delay_min = int(ord_item.delay_minutes) if ord_item.delay_minutes is not None else 0
        is_late = delay_min > 0 or (ord_item.is_on_time is False and delay_min > 0)
        if is_late:
            total_late += 1

        # Сводка зон
        if zone_name not in summary_zones:
            summary_zones[zone_name] = {"count": 0, "revenue": 0.0}
        summary_zones[zone_name]["count"] += 1
        summary_zones[zone_name]["revenue"] = round(summary_zones[zone_name]["revenue"] + amount, 2)

        # Сводка оплат
        if pay_name not in summary_payments:
            summary_payments[pay_name] = {"count": 0, "revenue": 0.0}
        summary_payments[pay_name]["count"] += 1
        summary_payments[pay_name]["revenue"] = round(summary_payments[pay_name]["revenue"] + amount, 2)

        # Запись дня
        if day_key not in days_map:
            days_map[day_key] = {
                "date": day_key,
                "date_formatted": local_dt.strftime("%d.%m.%Y"),
                "weekday": WEEKDAYS_RU[local_dt.weekday()],
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_check": 0.0,
                "late_count": 0,
                "on_time_count": 0,
                "on_time_percent": 100,
                "max_delay_minutes": 0,
                "zones": {},
                "payments": {},
                "orders_sample": []
            }

        d_entry = days_map[day_key]
        d_entry["total_orders"] += 1
        d_entry["total_revenue"] = round(d_entry["total_revenue"] + amount, 2)

        if is_late:
            d_entry["late_count"] += 1
            if delay_min > d_entry["max_delay_minutes"]:
                d_entry["max_delay_minutes"] = delay_min
        else:
            d_entry["on_time_count"] += 1

        # Зоны за день
        if zone_name not in d_entry["zones"]:
            d_entry["zones"][zone_name] = {"count": 0, "revenue": 0.0}
        d_entry["zones"][zone_name]["count"] += 1
        d_entry["zones"][zone_name]["revenue"] = round(d_entry["zones"][zone_name]["revenue"] + amount, 2)

        # Оплаты за день
        if pay_name not in d_entry["payments"]:
            d_entry["payments"][pay_name] = {"count": 0, "revenue": 0.0}
        d_entry["payments"][pay_name]["count"] += 1
        d_entry["payments"][pay_name]["revenue"] = round(d_entry["payments"][pay_name]["revenue"] + amount, 2)

        # Детали заказа
        address_str = ", ".join(filter(None, [ord_item.city, ord_item.street, f"д. {ord_item.house}" if ord_item.house else None])) or "Адрес не указан"
        d_entry["orders_sample"].append({
            "id": ord_item.id,
            "external_number": ord_item.external_number or str(ord_item.id),
            "amount": amount,
            "address": address_str,
            "zone": zone_name,
            "payment_method": pay_name,
            "delay_minutes": delay_min,
            "is_late": is_late,
            "created_time": local_dt.strftime("%H:%M")
        })

    # Сортировка дней и вычисление средних показателей
    days_list = []
    for d_k in sorted(days_map.keys(), reverse=True):
        entry = days_map[d_k]
        cnt = entry["total_orders"]
        entry["avg_check"] = round(entry["total_revenue"] / cnt, 2) if cnt > 0 else 0.0
        entry["on_time_percent"] = round((entry["on_time_count"] / cnt) * 100) if cnt > 0 else 100
        days_list.append(entry)

    avg_check = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    on_time_percent = round(((total_orders - total_late) / total_orders) * 100) if total_orders > 0 else 100

    return {
        "status": "success",
        "data": {
            "courier_name": target_name,
            "summary": {
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "avg_check": avg_check,
                "total_late": total_late,
                "on_time_percent": on_time_percent,
                "work_days_count": len(days_list),
                "zones": summary_zones,
                "payments": summary_payments
            },
            "days": days_list
        }
    }


def _find_order(db: Session, order_id: Any) -> Optional[Order]:
    """Поиск заказа по iiko_order_id (UUID) или локальному id (число)"""
    if not order_id:
        return None
    order_id_str = str(order_id).strip()
    order = db.exec(select(Order).where(Order.iiko_order_id == order_id_str)).first()
    if not order and order_id_str.isdigit():
        order = db.get(Order, int(order_id_str))
    return order

@router.get("/payment-types")
async def get_payment_types(
    db: Session = Depends(get_db)
):
    """Список типов оплаты, разрешенных для курьера"""
    settings = db.exec(select(IikoSettings)).first()
    if not settings:
        return {"status": "success", "data": []}
        
    pts = db.exec(select(PaymentType).where(PaymentType.is_active == True)).all()
    
    courier_cash_id = settings.payment_type_courier_cash or settings.payment_type_cash
    courier_card_id = settings.payment_type_courier_card or settings.payment_type_card

    data = []
    seen_ids = set()
    for pt in pts:
        is_courier_cash = (pt.iiko_id == courier_cash_id) if courier_cash_id else False
        is_courier_card = (pt.iiko_id == courier_card_id) if courier_card_id else False
        
        if is_courier_cash or is_courier_card:
            pt_dict = pt.dict()
            pt_dict["iiko_id"] = str(pt_dict["iiko_id"])
            pt_dict["is_courier_cash"] = is_courier_cash
            pt_dict["is_courier_card"] = is_courier_card
            data.append(pt_dict)
            seen_ids.add(str(pt.iiko_id))
            
    # Авто-фоллбэк, если курьерские типы не были явно настроены в админке
    has_cash = any(p.get("is_courier_cash") for p in data)
    has_card = any(p.get("is_courier_card") for p in data)
    
    if not has_cash:
        for pt in pts:
            if str(pt.iiko_id) in seen_ids:
                continue
            k = (pt.kind or "").lower()
            n = pt.name.lower()
            if k == "cash" or "нал" in n:
                pt_dict = pt.dict()
                pt_dict["iiko_id"] = str(pt_dict["iiko_id"])
                pt_dict["is_courier_cash"] = True
                pt_dict["is_courier_card"] = False
                data.append(pt_dict)
                seen_ids.add(str(pt.iiko_id))
                break

    if not has_card:
        for pt in pts:
            if str(pt.iiko_id) in seen_ids:
                continue
            k = (pt.kind or "").lower()
            n = pt.name.lower()
            if "курьер" in n and ("карт" in n or k == "card"):
                pt_dict = pt.dict()
                pt_dict["iiko_id"] = str(pt_dict["iiko_id"])
                pt_dict["is_courier_cash"] = False
                pt_dict["is_courier_card"] = True
                data.append(pt_dict)
                seen_ids.add(str(pt.iiko_id))
                break
        else:
            for pt in pts:
                if str(pt.iiko_id) in seen_ids:
                    continue
                k = (pt.kind or "").lower()
                n = pt.name.lower()
                if k == "card" or "карт" in n or "терминал" in n:
                    pt_dict = pt.dict()
                    pt_dict["iiko_id"] = str(pt_dict["iiko_id"])
                    pt_dict["is_courier_cash"] = False
                    pt_dict["is_courier_card"] = True
                    data.append(pt_dict)
                    seen_ids.add(str(pt.iiko_id))
                    break

    return {"status": "success", "data": data}

@router.post("/orders/{order_id}/accept")
async def accept_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Взятие заказа курьером на доставку"""
    settings = db.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки iiko не найдены")

    # Проверяем, привязан ли iiko_id к текущему пользователю
    if not current_user.iiko_id:
        raise HTTPException(
            status_code=400, 
            detail="У вашего аккаунта не привязан ID сотрудника iiko. Обратитесь к администратору."
        )

    # 1. Проверяем, открыта ли смена курьера в iiko (с кэшированием)
    try:
        logger.info(f"Checking if shift is open in iiko for courier {current_user.full_name} (iiko_id: {current_user.iiko_id})")
        terminal_groups = await iiko_service.get_courier_shifts(str(current_user.iiko_id))
        if not terminal_groups:
            logger.warning(f"Courier {current_user.full_name} does not have an open shift in iiko")
            raise HTTPException(
                status_code=400,
                detail="у вас не открыта смена , обратитесь к администратору"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking shift in iiko: {e}")
        raise HTTPException(
            status_code=400,
            detail="Не удалось проверить смену в iiko. Обратитесь к администратору."
        )

    # Находим заказ в локальной БД
    order = db.exec(select(Order).where(Order.iiko_order_id == order_id)).first()
    if not order and order_id.isdigit():
        order = db.get(Order, int(order_id))
        
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Проверяем, не назначен ли уже другой курьер
    if order.courier_name and order.courier_name != "Не назначен" and order.courier_name != "":
        raise HTTPException(status_code=400, detail=f"На этот заказ уже назначен курьер: {order.courier_name}")

    # 2. Назначаем курьера в iiko Cloud
    try:
        logger.info(f"Assigning courier {current_user.full_name} (iiko_id: {current_user.iiko_id}) to order {order_id} in iiko Cloud")
        res = await iiko_service.assign_delivery_courier(
            organization_id=settings.organization_id,
            order_id=str(order.iiko_order_id or order_id),
            courier_id=str(current_user.iiko_id)
        )
        if isinstance(res, dict) and res.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=f"Не удалось назначить курьера в iiko: {res.get('message', 'Неизвестная ошибка iiko API')}"
            )
    except HTTPException:
        raise
    except Exception as ae:
        logger.error(f"Failed to assign courier in iiko Cloud: {ae}")
        raise HTTPException(
            status_code=400,
            detail=f"Не удалось назначить курьера в iiko: {str(ae)}"
        )

    # 3. Обновляем локальный заказ в БД
    courier_name = current_user.employee.name if current_user.employee else current_user.full_name
    order.courier_name = courier_name
    
    if not order.status_history:
        order.status_history = []
        
    history_entry = {
        "status": order.status,
        "time": datetime.now(timezone.utc).isoformat(),
        "user": f"Courier:{current_user.full_name} (Self-assigned)"
    }
    order.status_history.append(history_entry)
    
    db.add(order)
    db.commit()
    db.refresh(order)

    # Отправляем уведомление курьеру
    try:
        from app.services.iiko_sync_service import iiko_sync_service
        await iiko_sync_service.send_order_notification(order, "courier_assigned", session=db)
    except Exception as notif_err:
        logger.error(f"Failed to send courier_assigned notification from take_order: {notif_err}")

    return {"status": "success", "message": "Вы успешно назначены на доставку", "courier_name": courier_name}

@router.post("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str, # Waiting, OnWay, Delivered
    payment_type_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Изменение статуса заказа курьером (Начать доставку / Доставлен / Готов)"""
    # 1. Находим заказ в БД по локальному ID или iiko_order_id
    order = _find_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    iiko_order_uuid = str(order.iiko_order_id) if order.iiko_order_id else str(order_id)
    settings = db.exec(select(IikoSettings)).first()
    org_id = None
    if order and order.branch and getattr(order.branch, "company", None) and order.branch.company.iiko_organization_id:
        org_id = str(order.branch.company.iiko_organization_id)
    elif settings and settings.organization_id:
        org_id = str(settings.organization_id)

    # Определяем iiko_id курьера
    courier_iiko_id = None
    if current_user.iiko_id:
        courier_iiko_id = str(current_user.iiko_id)
    elif getattr(current_user, "employee", None) and getattr(current_user.employee, "iiko_id", None):
        courier_iiko_id = str(current_user.employee.iiko_id)
    else:
        from app.models.employee import Employee
        emp = db.exec(select(Employee).where(
            (Employee.name == current_user.full_name) | (Employee.user_id == current_user.id)
        )).first()
        if emp and emp.iiko_id:
            courier_iiko_id = str(emp.iiko_id)

    try:
        # 2. Назначение курьера в iiko Cloud при начале доставки ("OnWay")
        if status == "OnWay" and courier_iiko_id and org_id and iiko_order_uuid:
            try:
                logger.info(f"Assigning courier {current_user.full_name} (iiko_id: {courier_iiko_id}) to order {order.id} ({iiko_order_uuid}) in iiko Cloud")
                res_assign = await iiko_service.assign_delivery_courier(
                    organization_id=org_id,
                    order_id=iiko_order_uuid,
                    courier_id=courier_iiko_id
                )
                if isinstance(res_assign, dict) and res_assign.get("status") == "error":
                    logger.warning(f"Warning assigning courier in iiko: {res_assign.get('message')}")
            except Exception as ae:
                logger.warning(f"Failed to assign courier in iiko Cloud (ignoring to proceed with status update): {ae}")

        # 3. Если статус Delivered и передан payment_type_id — фиксируем способ оплаты в iiko и БД с сохранением бонусов
        if status == "Delivered" and payment_type_id:
            try:
                await _apply_order_payment_to_iiko(
                    db=db,
                    order=order,
                    settings=settings,
                    payment_type_id=payment_type_id,
                    current_user=current_user
                )
            except Exception as pe:
                logger.error(f"Error applying payment on Delivered for order {order.id}: {pe}")

        # 4. Обновление статуса доставки в iiko Cloud
        res = None
        if org_id and iiko_order_uuid:
            try:
                logger.info(f"Changing delivery status for order {order.id} ({iiko_order_uuid}) to {status} in iiko Cloud")
                res = await iiko_service.change_delivery_status(
                    organization_id=org_id,
                    order_id=iiko_order_uuid,
                    delivery_status=status
                )
                if isinstance(res, dict) and res.get("status") == "error":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Не удалось перевести заказ в статус {status} в iiko: {res.get('message', 'Ошибка iiko API')}"
                    )
            except HTTPException:
                raise
            except Exception as se:
                logger.error(f"Error changing delivery status in iiko Cloud for order {order.id}: {se}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Не удалось перевести заказ в статус {status} в iiko: {str(se)}"
                )
        
        # 5. Мгновенное обновление статуса в локальной БД
        status_map = {
            "Waiting": OrderStatus.ready,
            "OnWay": OrderStatus.delivering,
            "Delivered": OrderStatus.delivered,
            "Closed": OrderStatus.closed
        }
        new_status = status_map.get(status)
        if new_status:
            logger.info(f"Updating local order {order.id} status to {new_status} (from courier API)")
            order.status = new_status
            if status == "OnWay":
                order.courier_name = current_user.employee.name if (getattr(current_user, "employee", None) and current_user.employee.name) else current_user.full_name
            
            # Добавление в историю статусов
            append_order_status_history(
                order=order,
                new_status=new_status,
                session=db,
                comment=f"Курьер: статус изменен на {status}",
                user=f"Курьер: {current_user.full_name or current_user.username}"
            )
            
            # Если доставлен, обновляем actual_time
            if new_status == OrderStatus.delivered:
                order.actual_time = datetime.now(timezone.utc).replace(tzinfo=None)
            
            db.add(order)
            db.commit()
            db.refresh(order)

            # Отправляем WebSocket уведомление в админку и всем курьерам в реальном времени
            try:
                from app.api.chat import manager
                ws_type = "order_delivered" if new_status == OrderStatus.delivered else "order_status_changed"
                ws_payload = {
                    "type": ws_type,
                    "order_id": order.id,
                    "order_number": order.external_number or str(order.id),
                    "status": new_status.value if hasattr(new_status, "value") else str(new_status),
                    "customer_name": order.customer_name or "Гость",
                    "order_type": order.order_type,
                    "courier_name": order.courier_name,
                    "total_amount": float(order.total_with_discount or order.total_amount or 0),
                    "delivery_address": order.delivery_address
                }
                manager.broadcast_sync(ws_payload)
            except Exception as ws_err:
                logger.debug(f"Failed to broadcast websocket status update from courier API: {ws_err}")

            # Отправляем уведомление клиенту о начале доставки
            if new_status == OrderStatus.delivering:
                try:
                    from app.services.iiko_sync_service import iiko_sync_service
                    await iiko_sync_service.send_order_notification(order, "order_delivering", session=db)
                except Exception as notif_err:
                    logger.error(f"Failed to send order_delivering notification: {notif_err}")

        return res or {"status": "success", "message": f"Статус заказа изменен на {status}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/acknowledge")
async def acknowledge_changes(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Сброс индикаторов изменений заказа (подтверждение курьером)"""
    from sqlalchemy.orm.attributes import flag_modified
    
    # Пытаемся найти по iiko_order_id (UUID), потом по внутреннему ID
    order = db.exec(select(Order).where(Order.iiko_order_id == order_id)).first()
    if not order and order_id.isdigit():
        order = db.get(Order, int(order_id))
        
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if order.change_indicators:
        logger.info(f"Acknowledging changes for order {order.id} (iiko: {order.iiko_order_id})")
        order.change_indicators = None
        db.add(order)
        db.commit()
        
    return {"status": "success"}

# --- Схемы для СБП QR (курьерская версия) ---
class CourierSbpQrRequestSchema(BaseModel):
    amount: float

@router.post("/orders/{order_id}/sbp-qr")
async def create_courier_sbp_qr(
    order_id: str,
    data: CourierSbpQrRequestSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Генерация динамического QR-кода СБП для оплаты заказа курьером (Т-Банк касса)"""
    order = _find_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    from app.models.tbank_settings import TBankSettings
    settings = db.exec(select(TBankSettings)).first()
    
    # Демо-ответ, если нет настроек Т-Банка или токена
    demo_qr = {
        "id": f"demo_sbp_qr_{order.id}",
        "url": f"https://qr.nspk.ru/AD1000787B2943B2943B2943B2943B29?orderId={order.id}",
        "svg": "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIiB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNmZmYiLz48cGF0aCBkPSJNMTAgMTBoODB2ODBIMTB6IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iNSIvPjxwYXRoIGQ9Ik0zMCAzMGg0MHY0MEgzMHoiIGZpbGw9IiMwMDAiLz48L3N2Zz4="
    }
    
    if not settings or not settings.is_active:
        logger.info(f"Т-Банк API не активен или не настроен. Возвращаем демо QR для заказа {order.id}")
        return {"status": "success", "data": demo_qr}

    from app.core.tbank_utils import generate_tbank_qrpay_signature, get_tbank_sbp_credentials
    mch_id, ter_id, secret_key = get_tbank_sbp_credentials(settings)

    import httpx
    import time
    import base64
    import io
    import qrcode
    import qrcode.image.svg
    from datetime import datetime

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY"
            
            out_transaction_no = str(int(time.time() * 100))
            amount_str = f"{data.amount:.2f}"
            
            payload = {
                "mchId": mch_id,
                "terId": ter_id,
                "currency": "643",
                "totalAmount": amount_str,
                "outTransactionNo": out_transaction_no,
                "subject": f"Оплата заказа №{order.external_number or order.id} в FoodZuka",
                "tradeType": "pay.paxpay.native",
                "version": "V1.0",
                "signType": "HMAC_SHA256",
                "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            payload["signature"] = generate_tbank_qrpay_signature(payload, secret_key, "qrpay")
            
            logger.info(f"Отправляем QRPAY в Т-Банк для заказа {order.id} (курьер): {out_transaction_no} (terId={ter_id})")
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                logger.warning(f"Ошибка QRPAY Т-Банк курьер ({res.status_code}): {res.text}")
                raise HTTPException(status_code=500, detail=f"Ошибка Т-Банк API ({res.status_code}): {res.text}")
                
            res_data = res.json()
            if res_data.get("code") != "SUCCESS":
                msg = res_data.get("msg") or res_data.get("message") or "Отклонено Т-Банком"
                logger.warning(f"Т-Банк отклонил QRPAY курьер: {res_data}")
                raise HTTPException(status_code=500, detail=f"Т-Банк отклонил генерацию QR: {msg}")
                
            out_trade_no = res_data.get("outTradeNo")
            code_url = res_data.get("codeUrl")
            if not out_trade_no or not code_url:
                logger.warning(f"Некорректные данные в ответе QRPAY Т-Банка (курьер): {res_data}")
                raise HTTPException(status_code=500, detail="Т-Банк не вернул QR-ссылку")
                
            # Генерируем SVG QR-кода на бэкенде
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(code_url)
            qr.make(fit=True)
            
            img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
            stream = io.BytesIO()
            img.save(stream)
            qr_svg_b64 = base64.b64encode(stream.getvalue()).decode('utf-8')
            
            return {
                "status": "success",
                "data": {
                    "id": f"tbank_qr_{out_trade_no}_{order.id}_{amount_str}",
                    "url": code_url,
                    "svg": qr_svg_b64
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Исключение при генерации QR-кода СБП курьером: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации QR-кода: {str(e)}")

@router.get("/orders/{order_id}/sbp-state/{qr_id}")
async def get_courier_sbp_state(
    order_id: str,
    qr_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Опрос статуса оплаты по СБП QR-коду курьером"""
    order = _find_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    # Разбираем упакованный ID для платежей
    if not qr_id.startswith("tbank_qr_"):
        return {"status": "success", "data": {"id": qr_id, "status": "CREATED", "amount": 0.0}}
        
    parts = qr_id.split("_")
    if len(parts) < 5:
        return {"status": "success", "data": {"id": qr_id, "status": "CREATED", "amount": 0.0}}
        
    out_trade_no = parts[2]
    amount_str = parts[4]
        
    from app.models.tbank_settings import TBankSettings
    settings = db.exec(select(TBankSettings)).first()
    if not settings or not settings.is_active:
        return {"status": "success", "data": {"id": qr_id, "status": "CREATED", "amount": 0.0}}

    from app.core.tbank_utils import generate_tbank_qrpay_signature, get_tbank_sbp_credentials
    mch_id, ter_id, secret_key = get_tbank_sbp_credentials(settings)
        
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QUERY"
    import httpx
    import time
    from datetime import datetime
    
    out_transaction_no = str(int(time.time() * 100))
    
    payload = {
        "mchId": mch_id,
        "terId": ter_id,
        "oriTransactionNo": out_trade_no,
        "outTransactionNo": out_transaction_no,
        "totalAmount": amount_str,
        "currency": "643",
        "tradeType": "pay.paxpay.native",
        "version": "V1.0",
        "signType": "HMAC_SHA256",
        "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    payload["signature"] = generate_tbank_qrpay_signature(payload, secret_key, "query")
    
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            logger.info(f"Запрашиваем QUERY для outTradeNo {out_trade_no} (terId={ter_id})...")
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                api_data = response.json()
                code_str = api_data.get("code")
                status_str = api_data.get("status", "")
                
                mapped_status = "CREATED"
                if code_str == "SUCCESS" and status_str in ["PAID", "SUCCESS"]:
                    mapped_status = "PAID"
                    amount_rub = float(amount_str)
                    
                    # 1. Если оплачено, автоматически обновляем статус оплаты в БД
                    from app.api.tbank_webhooks import process_order_payment
                    logger.info(f"Оплата СБП успешна для заказа {order.id} (Касса). Сумма: {amount_rub}")
                    process_order_payment(db, str(order.id), amount_rub, out_trade_no, "СБП (Т-Банк касса)")
                    
                    # 2. Регистрируем реальную транзакцию в tbank_statements
                    try:
                        from app.models.tbank_settings import TBankAccountStatement
                        existing_stmt = db.exec(
                            select(TBankAccountStatement).where(
                                TBankAccountStatement.payer_account == out_trade_no,
                                TBankAccountStatement.amount == float(amount_rub)
                            )
                        ).first()
                        
                        if not existing_stmt:
                            db_op = TBankAccountStatement(
                                account_number="СБП (T-API)",
                                charge_date=datetime.now(),
                                amount=float(amount_rub),
                                payment_purpose=f"Оплата СБП QR по заказу #{order.external_number or order.id} (T-Pay/СБП)",
                                payer_name=order.customer_name or "Физическое лицо (СБП)",
                                payer_inn="",
                                payer_account=out_trade_no,
                                payer_bank_bic="",
                                matched_order_id=order.id
                            )
                            db.add(db_op)
                            db.commit()
                            logger.info(f"Реальный платеж СБП {amount_rub}руб. (outTradeNo: {out_trade_no}) курьера сохранен в tbank_statements")
                    except Exception as stmt_err:
                        logger.error(f"Ошибка сохранения транзакции СБП курьера в tbank_statements: {stmt_err}")
                        db.rollback()
                        
                    # 3. Отправка WebSocket и Push-уведомления администратору в реальном времени
                    try:
                        from app.api.chat import manager
                        import asyncio
                        ws_payload = {
                            "type": "new_bank_payment",
                            "amount": float(amount_rub),
                            "method": "СБП (T-Pay)",
                            "customer": order.customer_name or "Физическое лицо (СБП)",
                            "order_id": order.id,
                            "rrn": out_trade_no
                        }
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                        if loop.is_running():
                            loop.create_task(manager.broadcast(ws_payload))
                            from app.services.iiko_sync_service import iiko_sync_service
                            loop.create_task(iiko_sync_service.send_admin_push_notification(
                                session=db,
                                title="Поступление оплаты!",
                                body=f"Сумма: {amount_rub:.2f} ₽ (СБП T-Pay) | Заказ #{order.external_number or order.id}",
                                url="/admin/bank/tbank-payments",
                                event_type="new_payment",
                                tag=f"payment-sbp-{out_trade_no}"
                            ))
                    except Exception as ws_err:
                        logger.error(f"Failed to send websocket payment notification from courier sbp: {ws_err}")
                        
                    # 4. Отправка Telegram-уведомления
                    try:
                        from app.api.tbank_webhooks import send_admin_telegram_notification
                        msg = (
                            f"⚡️ <b>Новый платеж по СБП (T-Pay)</b>\n"
                            f"💰 Сумма: <b>{amount_rub:.2f} ₽</b>\n"
                            f"📝 Заказ: <b>#{order.external_number or order.id}</b>\n"
                            f"👤 Клиент: {order.customer_name or 'Физическое лицо'}\n"
                            f"🆔 RRN/QR: {out_trade_no}\n"
                            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                        )
                        send_admin_telegram_notification(msg, db)
                    except Exception as tg_err:
                        logger.error(f"Failed to send telegram sbp notification: {tg_err}")
                    
                return {"status": "success", "data": {"id": qr_id, "status": mapped_status, "amount": float(amount_str) if mapped_status == "PAID" else 0.0}}
                
        return {"status": "success", "data": {"id": qr_id, "status": "CREATED", "amount": 0.0}}
    except Exception as e:
        logger.warning(f"Ошибка опроса статуса QR СБП Т-Банк: {str(e)}.")
        return {"status": "success", "data": {"id": qr_id, "status": "CREATED", "amount": 0.0}}

@router.post("/orders/{order_id}/sbp-simulate-pay")
async def simulate_sbp_payment(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Имитация успешной оплаты по СБП для демо-режима"""
    order = _find_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    from app.api.tbank_webhooks import process_order_payment
    amount = float(order.left_to_pay if order.left_to_pay > 0 else (order.total_with_discount or order.total_amount))
    
    success = process_order_payment(db, str(order.id), amount, "RRN_DEMO_SBP", "СБП (QR-код/Тест)")
    if success:
        return {"status": "success", "message": "Оплата успешно сэмулирована"}
    else:
        raise HTTPException(status_code=500, detail="Не удалось обработать оплату")


# --- Схема отправки QR-кода клиенту ---
class CourierShareQrRequest(BaseModel):
    channel: str # vk, tg, max
    qr_url: str
    amount: float

@router.post("/orders/{order_id}/share-qr")
async def share_courier_sbp_qr(
    order_id: str,
    data: CourierShareQrRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отправка ссылки и QR-кода оплаты по СБП в выбранную соцсеть клиента"""
    order = _find_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    from app.models.customer import Customer
    customer = None
    if order.customer_id:
        customer = db.get(Customer, order.customer_id)
    if not customer and order.customer_phone:
        # Нормализуем телефон
        clean_p = "".join(filter(str.isdigit, order.customer_phone))
        if len(clean_p) == 10:
            clean_p = "7" + clean_p
        elif len(clean_p) == 11 and clean_p.startswith("8"):
            clean_p = "7" + clean_p[1:]
        clean_p = "+" + clean_p
        customer = db.exec(select(Customer).where(Customer.phone == clean_p)).first()
        if not customer:
            customer = db.exec(select(Customer).where(Customer.phone.like(f"%{clean_p[-10:]}"))).first()

    if not customer:
        raise HTTPException(status_code=400, detail="Не удалось найти профиль клиента для отправки")

    # Генерируем PNG-изображение QR-кода на основе url
    import qrcode
    import os
    import time
    qr_dir = "/app/media/img/qr"
    os.makedirs(qr_dir, exist_ok=True)
    file_path = f"{qr_dir}/share_order_{order_id}_{int(time.time())}.png"
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data.qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(file_path, "PNG")
    except Exception as e:
        logger.error(f"Failed to generate share QR image: {e}")
        file_path = None

    message_text = f"Оплата заказа №{order.external_number or order.id} на сумму {data.amount:.2f} руб. по СБП."

    shared_msg_id = None
    chat_id = None
    
    if data.channel == "vk":
        from app.models.vk_user import VkUser
        vk_user = None
        if customer.vk_user_id:
            vk_user = db.exec(select(VkUser).where(VkUser.vk_id == customer.vk_user_id)).first()
        if not vk_user and customer.phone:
            clean_phone = "".join(filter(str.isdigit, customer.phone))
            vk_user = db.exec(select(VkUser).where(VkUser.phone.like(f"%{clean_phone[-10:]}"))).first()
            
        if not vk_user or not vk_user.vk_id:
            raise HTTPException(status_code=400, detail="У клиента не привязан ВКонтакте")
            
        from app.services.vk_bot_service import vk_bot_service
        bot_token = vk_bot_service._get_bot_token()
        if not bot_token:
            raise HTTPException(status_code=400, detail="VK токен не настроен")
            
        from app.services.vk_service import send_vk_message
        res = await send_vk_message(
            vk_id=vk_user.vk_id,
            message=message_text,
            bot_token=bot_token,
            image_path=file_path
        )
        if not res:
            raise HTTPException(status_code=400, detail="Не удалось отправить сообщение в VK")
            
        shared_msg_id = str(res)
        chat_id = str(vk_user.vk_id)

    elif data.channel == "tg" or data.channel == "telegram":
        telegram_id = customer.telegram_id or order.telegram_user_id
        if not telegram_id:
            raise HTTPException(status_code=400, detail="У клиента не привязан Telegram")
            
        from app.services.vk_notification_router import get_telegram_token
        tg_token = get_telegram_token(db)
        if not tg_token:
            raise HTTPException(status_code=400, detail="Telegram токен не настроен")
            
        import httpx
        url = f"https://api.telegram.org/bot{tg_token}/sendPhoto"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(file_path, "rb") as f:
                    files = {"photo": f}
                    payload = {
                        "chat_id": telegram_id,
                        "caption": message_text,
                        "parse_mode": "HTML"
                    }
                    response = await client.post(url, data=payload, files=files)
                    if response.status_code == 200:
                        res_data = response.json()
                        if res_data.get("ok"):
                            shared_msg_id = str(res_data.get("result", {}).get("message_id"))
                            chat_id = str(telegram_id)
        except Exception as e:
            logger.error(f"Failed to send Telegram photo: {e}")
            
        if not shared_msg_id:
            raise HTTPException(status_code=400, detail="Не удалось отправить сообщение в Telegram")

    elif data.channel == "max":
        from app.services.vk_notification_router import send_max_message_helper
        max_target = customer.max_user_id or customer.phone
        if not max_target:
            raise HTTPException(status_code=400, detail="У клиента не привязан MAX ID / телефон")
            
        public_url = f"https://vezuroll.ru/media/img/qr/{os.path.basename(file_path)}"
        max_text = f"{message_text}\n\nСсылка на оплату СБП: {public_url}"
        
        success = await send_max_message_helper(max_target, max_text, db)
        if not success:
            raise HTTPException(status_code=400, detail="Не удалось отправить сообщение в MAX")
            
        shared_msg_id = "max_sent"
        chat_id = max_target
    else:
        raise HTTPException(status_code=400, detail="Неверный канал")

    from app.models.vk_bot import OrderPaymentQrShare
    share = OrderPaymentQrShare(
        order_id=order.id,
        channel=data.channel,
        chat_id=chat_id,
        message_id=shared_msg_id
    )
    db.add(share)
    db.commit()
    
    return {"status": "success", "message_id": shared_msg_id}


def _extract_bonus_payments(iiko_order: Optional[Dict[str, Any]], order: Order, db: Session) -> List[Dict[str, Any]]:
    """
    Надежное извлечение оплат бонусами (IikoCard / LoyaltyCard / Бонусная система) из заказа iiko.
    Если бонусы в iiko проведены как скидка (discounts), они не являются платежом и не должны попадать в payments.
    Если же бонусы в iiko оформлены именно как платеж в payments, сохраняем их с корректным paymentTypeKind и paymentAdditionalData.
    """
    bonus_payments = []
    seen_ids = set()

    if not iiko_order:
        return bonus_payments

    order_body = iiko_order.get("order") or iiko_order
    
    # 1. Проверяем, учтены ли бонусы уже в скидках (discounts) iiko
    raw_discounts = order_body.get("discounts") or []
    has_bonus_in_discounts = any(
        "iikocard" in ((d.get("discountType") or {}).get("name") or "").lower() or
        "бонус" in ((d.get("discountType") or {}).get("name") or "").lower()
        for d in raw_discounts if isinstance(d, dict)
    )
    
    # Если бонусы уже учтены в discounts iiko, они уменьшают сумму чека и не являются отдельным платежом в payments.
    # Добавлять их в payments нельзя — это сломает сумму чека и вызовет ошибку 400 Bad Request.
    if has_bonus_in_discounts:
        logger.info(f"Order {order.id}: бонусы уже учтены в discounts iiko, отдельный платеж в payments не требуется")
        return []

    # 2. Если в discounts бонусов нет, проверяем, были ли они изначально в payments заказа iiko
    raw_payments = order_body.get("payments") or []
    for p in raw_payments:
        if not isinstance(p, dict):
            continue
        pt = p.get("paymentType") or {}
        pn = ((pt.get("name") if isinstance(pt, dict) else "") or "").lower()
        pk = ((p.get("paymentTypeKind") or p.get("kind") or (pt.get("kind") if isinstance(pt, dict) else "") or "") or "").lower()
        
        # Проверяем, является ли платеж списанием бонусов
        if pk in ["iikocard", "loyaltycard"] or "бонус" in pn or "bonus" in pn:
            pt_id = p.get("paymentTypeId") or (pt.get("id") if isinstance(pt, dict) else None)
            if not pt_id:
                continue
            pt_id_str = str(pt_id)
            if pt_id_str in seen_ids:
                continue
            seen_ids.add(pt_id_str)
            
            # Для iiko Transport API вид платежа для карт лояльности — LoyaltyCard с paymentAdditionalData
            customer_phone = order.customer_phone or (order_body.get("phone") or "")
            clean_phone = "".join(filter(str.isdigit, customer_phone))
            if clean_phone.startswith("8") and len(clean_phone) == 11:
                clean_phone = "7" + clean_phone[1:]
            if clean_phone and not clean_phone.startswith("+"):
                clean_phone = "+" + clean_phone
                
            bonus_item = {
                "paymentTypeKind": "LoyaltyCard",
                "sum": float(p.get("sum") or 0),
                "paymentTypeId": pt_id_str,
                "isProcessedExternally": False,
                "isFiscalizedExternally": False
            }
            if clean_phone:
                bonus_item["paymentAdditionalData"] = {
                    "searchScope": "Phone",
                    "credential": clean_phone
                }
            bonus_payments.append(bonus_item)

    return bonus_payments


def _calculate_residual_sum(order: Order, bonus_payments: List[Dict[str, Any]], target_amount: Optional[float] = None) -> float:
    """
    Расчет остаточной стоимости заказа для оплаты курьеру строго за вычетом бонусов.
    """
    bonus_sum = sum(float(bp.get("sum") or 0) for bp in bonus_payments)
    
    # 1. Если есть реальные бонусные платежи в массиве payments, вычитаем их
    if bonus_sum > 0:
        total_order_sum = float(order.total_amount or 0)
        return max(0.0, round(total_order_sum - bonus_sum, 2))
        
    # 2. Если у заказа есть total_with_discount (сумма чека со скидками и списанными бонусами)
    if getattr(order, "total_with_discount", None) and float(order.total_with_discount) > 0:
        return float(order.total_with_discount)
        
    # 3. Если у заказа есть left_to_pay
    if getattr(order, "left_to_pay", None) and float(order.left_to_pay) > 0:
        return float(order.left_to_pay)
        
    # 4. Фолбэк на target_amount или total_amount
    total_order_sum = float(order.total_amount or 0)
    return float(target_amount if target_amount is not None else total_order_sum)


async def _apply_order_payment_to_iiko(
    db: Session,
    order: Order,
    settings: Optional[IikoSettings],
    payment_type_id: str,
    current_user: User,
    amount: Optional[float] = None
) -> Tuple[bool, Optional[str]]:
    """
    Универсальная функция применения курьерского способа оплаты в iiko Cloud API с сохранением бонусов.
    Возвращает (success, payment_name).
    """
    org_id = settings.organization_id if settings else None
    
    # 1. Находим PaymentType в БД
    pt_db = db.exec(select(PaymentType).where(
        (PaymentType.iiko_id == payment_type_id) | (PaymentType.id == int(payment_type_id) if payment_type_id.isdigit() else False)
    )).first()
    if not pt_db:
        logger.warning(f"PaymentType with ID {payment_type_id} not found in DB")
        return False, None

    selected_pt_name = pt_db.name
    real_pt_iiko_id = str(pt_db.iiko_id)
    
    if org_id and order.iiko_order_id:
        try:
            # Получаем актуальный заказ из iiko для выделения бонусов
            iiko_order = await iiko_service.get_order_by_id(
                order_id=order.iiko_order_id,
                organization_id=org_id,
                api_login=settings.api_login if settings else None
            )
            
            # Извлекаем бонусы
            bonus_payments = _extract_bonus_payments(iiko_order, order, db)
            
            # Рассчитываем остаточную сумму строго за вычетом бонусов
            pay_sum = _calculate_residual_sum(order, bonus_payments, amount)
            
            # Определяем kind платежа
            if settings and (real_pt_iiko_id == settings.payment_type_courier_cash or real_pt_iiko_id == settings.payment_type_cash):
                pt_kind = "Cash"
            elif settings and (real_pt_iiko_id == settings.payment_type_courier_card or real_pt_iiko_id == settings.payment_type_card):
                pt_kind = "Card"
            elif pt_db.kind and pt_db.kind in ["Cash", "Card", "LoyaltyCard", "External"]:
                pt_kind = pt_db.kind
            else:
                pt_kind = "Cash"
                
            new_payments = [{
                "paymentTypeKind": pt_kind,
                "sum": pay_sum,
                "paymentTypeId": real_pt_iiko_id,
                "isProcessedExternally": False,
                "isFiscalizedExternally": False
            }]
            
            final_payments = bonus_payments + new_payments
            
            # Проверяем, не совпадает ли уже оплата в iiko
            order_body = iiko_order.get("order") or iiko_order
            raw_payments = order_body.get("payments") or []
            payments_already_match = False
            if len(final_payments) == 1 and len(raw_payments) == 1:
                cur_p = raw_payments[0]
                cur_pt_id = str(cur_p.get("paymentTypeId") or (cur_p.get("paymentType") or {}).get("id") or "")
                cur_sum = round(float(cur_p.get("sum") or 0), 2)
                new_p = final_payments[0]
                new_pt_id = str(new_p.get("paymentTypeId") or "")
                new_sum = round(float(new_p.get("sum") or 0), 2)
                if cur_pt_id == new_pt_id and abs(cur_sum - new_sum) < 0.05:
                    payments_already_match = True

            if not payments_already_match:
                logger.info(f"Applying payment in iiko for order {order.id} ({order.iiko_order_id}): bonus_count={len(bonus_payments)}, residual_sum={pay_sum}, final_payments={final_payments}")
                res = await iiko_service.change_order_payments(
                    organization_id=org_id,
                    order_id=order.iiko_order_id,
                    payments=final_payments,
                    api_login=settings.api_login if settings else None
                )
                if isinstance(res, dict) and res.get("status") == "error":
                    logger.error(f"iiko change_payments returned error for order {order.id}: {res}")
            else:
                logger.info(f"Order {order.id}: payment already matches in iiko, skipping change_payments API call")
        except Exception as pe:
            logger.error(f"Error applying payments in iiko for order {order.id}: {pe}")

    # Обновляем заказ в локальной БД
    order.payment_method = selected_pt_name
    if not order.status_history:
        order.status_history = []
    order.status_history.append({
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "time": datetime.now(timezone.utc).isoformat(),
        "user": f"Courier:{current_user.full_name} (Выбран способ оплаты {selected_pt_name})"
    })
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return True, selected_pt_name


class CourierChangePaymentItem(BaseModel):
    payment_type_id: str
    sum: float

class CourierChangePaymentTypeRequestSchema(BaseModel):
    payments: List[CourierChangePaymentItem]

@router.post("/orders/{order_id}/change-payment-type")
async def courier_change_payment_type(
    order_id: str,
    data: CourierChangePaymentTypeRequestSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Смена способа оплаты заказа курьером (в пути) с сохранением бонусов"""
    logger.info(f"Courier {current_user.full_name} requested payment change for order {order_id} to: {data.payments}")
    order = _find_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    settings = db.exec(select(IikoSettings)).first()
    if not settings or not settings.organization_id:
        raise HTTPException(status_code=400, detail="Интеграция с iiko не настроена")
        
    org_id = settings.organization_id
    
    # 1. Получаем свежие данные заказа из iiko
    iiko_order = None
    if order.iiko_order_id:
        try:
            iiko_order = await iiko_service.get_order_by_id(
                order_id=order.iiko_order_id,
                organization_id=org_id,
                api_login=settings.api_login
            )
        except Exception as e:
            logger.error(f"Failed to fetch order from iiko: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка связи с iiko: {str(e)}")
            
        if not iiko_order:
            raise HTTPException(status_code=400, detail="Заказ не найден в iiko")
        
    # 2. Надежно выделяем оплаты бонусами (IikoCard/LoyaltyCard) из iiko_order
    bonus_payments = _extract_bonus_payments(iiko_order, order, db)
    residual_sum = _calculate_residual_sum(order, bonus_payments)

    # 3. Составляем новый список оплат
    new_payments = []
    selected_names = []
    for new_p in data.payments:
        pt_id = str(new_p.payment_type_id)
        # Если одиночный выбор - сумма строго равна остаточной стоимости чека
        if len(data.payments) == 1:
            psum = residual_sum
        else:
            psum = float(new_p.sum)
        
        # Загружаем PaymentType из БД
        pt_db = db.exec(select(PaymentType).where(
            (PaymentType.iiko_id == pt_id) | (PaymentType.id == int(pt_id) if pt_id.isdigit() else False)
        )).first()
        if not pt_db:
            raise HTTPException(status_code=400, detail=f"Тип оплаты с ID {pt_id} не найден в БД")
            
        selected_names.append(pt_db.name)
        real_pt_iiko_id = str(pt_db.iiko_id)
        
        # Определяем kind на основании сопоставления курьера
        if real_pt_iiko_id == settings.payment_type_courier_cash or real_pt_iiko_id == settings.payment_type_cash:
            pt_kind = "Cash"
        elif real_pt_iiko_id == settings.payment_type_courier_card or real_pt_iiko_id == settings.payment_type_card:
            pt_kind = "Card"
        elif pt_db.kind:
            pt_kind = pt_db.kind
        else:
            pt_kind = "Cash"
            
        new_payments.append({
            "paymentTypeKind": pt_kind,
            "sum": psum,
            "paymentTypeId": real_pt_iiko_id,
            "isProcessedExternally": False,
            "isFiscalizedExternally": False
        })
        
    # Объединяем бонусы и новые платежи: бонусы сохраняются!
    final_payments = bonus_payments + new_payments
    
    # 4. Проверяем, не совпадает ли уже оплата в iiko
    order_body = iiko_order.get("order") or iiko_order
    raw_payments = order_body.get("payments") or []
    payments_already_match = False
    if len(final_payments) == 1 and len(raw_payments) == 1:
        cur_p = raw_payments[0]
        cur_pt_id = str(cur_p.get("paymentTypeId") or (cur_p.get("paymentType") or {}).get("id") or "")
        cur_sum = round(float(cur_p.get("sum") or 0), 2)
        new_p = final_payments[0]
        new_pt_id = str(new_p.get("paymentTypeId") or "")
        new_sum = round(float(new_p.get("sum") or 0), 2)
        if cur_pt_id == new_pt_id and abs(cur_sum - new_sum) < 0.05:
            payments_already_match = True

    # Отправляем изменения в iiko только если способ оплаты реально изменился
    if order.iiko_order_id and not payments_already_match:
        try:
            logger.info(f"Changing payments for order {order.id} in iiko. Bonus count: {len(bonus_payments)}, New payments: {new_payments}")
            res = await iiko_service.change_order_payments(
                organization_id=org_id,
                order_id=order.iiko_order_id,
                payments=final_payments,
                api_login=settings.api_login
            )
            if isinstance(res, dict) and res.get("status") == "error":
                raise HTTPException(status_code=400, detail=f"Ошибка iiko: {res.get('message', 'Не удалось изменить оплату')}")
        except HTTPException:
            raise
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Failed to change payments in iiko for order {order.id}: {err_str}")
            # Если заказ в iiko уже закрыт или пречек напечатан на кассе, не блокируем курьера
            is_already_closed_or_processed = (
                (order_body.get("status") or "").lower() == "closed" or
                "closed" in err_str.lower() or
                "processed" in err_str.lower()
            )
            if is_already_closed_or_processed:
                logger.info(f"Order {order.id} is already closed/processed in iiko. Updating local payment method.")
            else:
                err_detail = None
                if hasattr(e, "response") and e.response is not None:
                    try:
                        err_body = e.response.json()
                        err_detail = err_body.get("errorDescription") or err_body.get("message")
                    except Exception:
                        pass
                raise HTTPException(status_code=400, detail=f"Не удалось сменить оплату в iiko: {err_detail or err_str}")
    elif payments_already_match:
        logger.info(f"Order {order.id}: payment already matches in iiko, skipping change_payments API call")
        
    # 5. Обновляем локальный заказ
    if selected_names:
        order.payment_method = ", ".join(selected_names)
        
    if not order.status_history:
        order.status_history = []
    order.status_history.append({
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "time": datetime.now(timezone.utc).isoformat(),
        "user": f"Courier:{current_user.full_name} (Смена оплаты на {order.payment_method})"
    })
    db.add(order)
    db.commit()
    db.refresh(order)

    # 6. Принудительно запускаем синхронизацию этого заказа, чтобы обновить БД
    # Оповещаем WebSocket шину о смене метода оплаты без затирания мгновенным sync_order_by_id
    try:
        from app.api.chat import manager
        manager.broadcast_sync({
            "type": "change_payments",
            "order_id": order.id,
            "order_number": order.external_number or str(order.id),
            "payment_method": order.payment_method
        })
    except Exception as ws_err:
        logger.debug(f"Failed to broadcast payment change WS: {ws_err}")
        
    return {"status": "success", "message": "Способ оплаты успешно изменен"}


class CourierCloseOrderRequestSchema(BaseModel):
    payment_type_id: Optional[str] = None
    amount: Optional[float] = None

@router.post("/orders/{order_id}/close")
async def close_courier_order(
    order_id: str,
    payment_type_id: Optional[str] = None,
    amount: Optional[float] = None,
    body: Optional[CourierCloseOrderRequestSchema] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Завершение и закрытие доставки курьером с фиксацией способа оплаты и сохранением бонусов.
    """
    target_payment_type_id = (body.payment_type_id if body and body.payment_type_id else None) or payment_type_id
    target_amount = (body.amount if body and body.amount is not None else None) if amount is None else amount

    order = _find_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    settings = db.exec(select(IikoSettings)).first()
    org_id = settings.organization_id if settings else None
    
    # 1. Если передан тип оплаты и есть привязка к iiko - обновляем оплату в iiko с сохранением бонусов
    selected_pt_name = None
    if target_payment_type_id:
        success, pt_name = await _apply_order_payment_to_iiko(
            db=db,
            order=order,
            settings=settings,
            payment_type_id=target_payment_type_id,
            current_user=current_user,
            amount=target_amount
        )
        if success:
            selected_pt_name = pt_name
            
    # 2. Закрываем доставку в iiko Cloud
    if org_id and order.iiko_order_id:
        try:
            logger.info(f"Closing delivery order {order.id} ({order.iiko_order_id}) in iiko Cloud")
            await iiko_service.close_delivery(
                organization_id=org_id,
                order_id=order.iiko_order_id,
                api_login=settings.api_login if settings else None
            )
        except Exception as ce:
            logger.warning(f"Error closing delivery in iiko for order {order.id}: {ce}")

    # 3. Обновляем статус и оплату в локальной БД
    order.status = OrderStatus.closed
    order.is_paid = True
    order.left_to_pay = Decimal("0.00")
    if selected_pt_name:
        order.payment_method = selected_pt_name
    order.actual_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    append_order_status_history(
        order=order,
        new_status=OrderStatus.closed,
        session=db,
        comment="Заказ доставлен и закрыт курьером",
        user=f"Курьер: {current_user.full_name or current_user.username}"
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # 4. WebSocket уведомление о закрытии заказа без гонки затирания
    try:
        from app.api.chat import manager
        manager.broadcast_sync({
            "type": "order_delivered",
            "order_id": order.id,
            "order_number": order.external_number or str(order.id),
            "status": "closed",
            "customer_name": order.customer_name or "Гость",
            "courier_name": order.courier_name
        })
    except Exception as ws_err:
        logger.debug(f"Failed to broadcast close WS: {ws_err}")

    return {
        "status": "success",
        "message": "Заказ успешно доставлен и закрыт",
        "order_id": order.id,
        "status_name": OrderStatus.closed.value
    }


