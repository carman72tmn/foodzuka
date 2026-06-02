from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import logging

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
        
        # Фильтрация по курьеру (если не суперюзер)
        if not current_user.is_superuser:
            # Сопоставляем по имени (как оно сохраняется из iiko в sync_service)
            query = query.where(Order.courier_name == current_user.full_name)
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
            if courier_filter:
                df_local = (now_local - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
                logger.info(f"Default archive filter for courier {courier_filter} (7 days)")
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
                "courier_name": o.courier_name or "Не назначен",
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "expected_time": o.expected_time.isoformat() if o.expected_time else None,
                "actual_time": o.actual_time.isoformat() if o.actual_time else None,
                "delay_minutes": o.delay_minutes,
                "on_the_way_time": next((h.get("time") for h in reversed(o.status_history or []) if h.get("status") == "delivering"), None),
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

@router.get("/active-couriers")
async def get_active_couriers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Просмотр активных курьеров (только для Супер Админа)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
        
    settings = db.exec(select(IikoSettings)).first()
    try:
        couriers = await iiko_service.get_active_couriers(
            organization_id=settings.organization_id
        )
        
        if isinstance(couriers, dict) and couriers.get("status") == "error":
            error_code = couriers.get("error")
            if error_code in ["IIKO_RIGHTS_ERROR", "UNAUTHORIZED"]:
                logger.warning(f"Iiko Couriers Access Denied. Falling back to local DB orders.")
                # ФОЛЛБЭК: Берем курьеров из заказов за последние 24 часа
                yesterday = datetime.now() - timedelta(days=1)
                recent_couriers = db.exec(
                    select(Order.courier_name)
                    .where(Order.actual_time > yesterday)
                    .where(Order.courier_name != None)
                    .distinct()
                ).all()
                
                fallback_data = []
                for name in recent_couriers:
                    fallback_data.append({
                        "id": name, # Используем имя как ID если нет iiko_id
                        "name": name,
                        "latitude": None,
                        "longitude": None,
                        "is_fallback": True
                    })
                return {"status": "success", "data": fallback_data}
            raise HTTPException(status_code=400, detail=couriers.get("message"))
            
        return {"status": "success", "data": couriers}
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "403" in err_str or "RIGHTS" in err_str.upper():
            logger.warning(f"Iiko Couriers Access Denied (Exception). Falling back to local DB orders.")
            # Аналогичный фоллбэк для исключений
            yesterday = datetime.now() - timedelta(days=1)
            recent_couriers = db.exec(
                select(Order.courier_name)
                .where(Order.actual_time > yesterday)
                .where(Order.courier_name != None)
                .distinct()
            ).all()
            return {"status": "success", "data": [{"id": n, "name": n, "is_fallback": True} for n in recent_couriers]}
        logger.error(f"Error fetching active couriers: {e}")
        return {"status": "success", "data": []}

@router.get("/payment-types")
async def get_payment_types(
    db: Session = Depends(get_db)
):
    """Список активных типов оплаты из нашей БД (синхронизированных с iiko)"""
    pts = db.exec(select(PaymentType).where(PaymentType.is_active == True)).all()
    # Явное преобразование в dict и UUID в str для исключения ошибок Pydantic
    data = []
    for pt in pts:
        pt_dict = pt.dict()
        if pt_dict.get("iiko_id"):
            pt_dict["iiko_id"] = str(pt_dict["iiko_id"])
        data.append(pt_dict)
        
    return {"status": "success", "data": data}

@router.post("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str, # Waiting, OnWay, Delivered
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Изменение статуса заказа"""
    settings = db.exec(select(IikoSettings)).first()
    try:
        # Update in iiko
        res = await iiko_service.change_delivery_status(
            organization_id=settings.organization_id,
            order_id=order_id,
            delivery_status=status
        )
        
        # [RESPONSIVE] Update local DB status immediately
        order = db.exec(select(Order).where(Order.iiko_order_id == order_id)).first()
        if not order and order_id.isdigit():
            order = db.get(Order, int(order_id))
            
        if order:
            # Map iiko status to our OrderStatus enum
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
                
                # Add to history if not present
                if not order.status_history:
                    order.status_history = []
                
                history_entry = {
                    "status": new_status,
                    "time": datetime.now(timezone.utc).isoformat(),
                    "user": f"Courier:{current_user.full_name}"
                }
                order.status_history.append(history_entry)
                
                # If delivered, update actual_time
                if new_status == OrderStatus.delivered:
                    order.actual_time = datetime.now(timezone.utc).replace(tzinfo=None)
                
                db.add(order)
                db.commit()

        return res
    except Exception as e:
        logger.error(f"Error updating order status {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/close")
async def close_order(
    order_id: str,
    payment_type_id: str,
    amount: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Финальное закрытие заказа с оплатой"""
    settings = db.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки iiko не найдены")

    # 1. Получаем информацию о типе оплаты
    pt = db.exec(select(PaymentType).where(PaymentType.iiko_id == payment_type_id)).first()
    if not pt:
        raise HTTPException(status_code=404, detail="Тип оплаты не найден")
    
    try:
        # 2. Добавляем оплату к заказу
        payment_payload = [
            {
                "paymentTypeKind": pt.kind or "Cash",
                "sum": amount,
                "paymentTypeId": payment_type_id,
                "isProcessedExternally": pt.is_processed_externally
            }
        ]
        
        await iiko_service.change_order_payments(
            organization_id=settings.organization_id,
            order_id=order_id,
            payments=payment_payload
        )
        
        # 3. Закрываем заказ
        res = await iiko_service.close_delivery(
            organization_id=settings.organization_id,
            order_id=order_id
        )
        return {"status": "success", "data": res}
    except Exception as e:
        logger.error(f"Error closing order {order_id}: {e}")
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
