"""
Сервис расчета показателей рабочих смен сотрудников (выручка поваров, курьеров, администраторов).
"""
from typing import Optional, Dict, Any, Set
from datetime import datetime, timezone
from sqlmodel import Session, select
from sqlalchemy import func

from app.models.employee import Employee, Shift
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import KitchenZone, Product
import logging

logger = logging.getLogger(__name__)


def is_cook_employee(emp: Optional[Employee]) -> bool:
    """Проверяет, является ли сотрудник поваром/работником кухни"""
    if not emp:
        return False
    role = (emp.role or "").lower()
    name = (emp.name or "").lower()
    return (
        any(k in role for k in ["повар", "кухн", "горяч", "шеф", "суши", "пицц", "cook"])
        or any(k in name for k in ["повар", "кухн", "горяч", "cook"])
    )


def is_courier_employee(emp: Optional[Employee]) -> bool:
    """Проверяет, является ли сотрудник курьером"""
    if not emp:
        return False
    role = (emp.role or "").lower()
    name = (emp.name or "").lower()
    return (
        "курьер" in role or "courier" in role or role in ["cur", "cour"]
        or "курьер" in name or "courier" in name or getattr(emp, "is_courier", False)
    )


def is_admin_employee(emp: Optional[Employee]) -> bool:
    """Проверяет, является ли сотрудник администратором/кассиром"""
    if not emp:
        return False
    role = (emp.role or "").lower()
    name = (emp.name or "").lower()
    return any(k in role for k in ["администратор", "оператор", "manager", "старший", "adm", "admin", "кассир"])


def get_cook_kitchen_zones(session: Session) -> tuple[Set[int], Set[int]]:
    """
    Возвращает кортеж (kitchen_zone_ids, hot_zone_ids).
    По умолчанию в БД: 2 - Кухня, 3 - Горячий цех.
    """
    kitchen_zone_ids = set()
    hot_zone_ids = set()
    try:
        zones = session.exec(select(KitchenZone)).all()
        for z in zones:
            name_lower = (z.name or "").lower()
            if any(k in name_lower for k in ["горяч", "hot"]):
                hot_zone_ids.add(z.id)
            elif any(k in name_lower for k in ["кухн", "kitchen"]):
                kitchen_zone_ids.add(z.id)
    except Exception as e:
        logger.error(f"Error fetching kitchen zones: {e}")

    if not kitchen_zone_ids:
        kitchen_zone_ids.add(2)
    if not hot_zone_ids:
        hot_zone_ids.add(3)

    return kitchen_zone_ids, hot_zone_ids


def calculate_shift_metrics(
    session: Session,
    shift: Shift,
    employee: Optional[Employee] = None
) -> Dict[str, Any]:
    """
    Рассчитывает выручку и метрики смены:
    - С момента выхода в смену (date_open) и до закрытия (date_close),
      либо до текущего момента UTC, если смена еще открыта.
    - Для поваров: выручка по цеху «Кухня» и цеху «Горячий цех» (с учетом скидок чека).
    - Для курьеров: сумма доставленных/закрытых заказов курьера.
    - Для администраторов: сумма заказов кассы / заведения.
    - Количество отмененных заказов за время смены.
    """
    emp = employee or shift.employee
    if not emp and shift.employee_id:
        emp = session.get(Employee, shift.employee_id)

    start_dt = shift.date_open
    end_dt = shift.date_close if shift.date_close else datetime.now(timezone.utc)

    # Приводим к naive UTC для корректного сравнения с Order.created_at в БД
    if start_dt and start_dt.tzinfo:
        start_dt = start_dt.astimezone(timezone.utc).replace(tzinfo=None)
    if end_dt and end_dt.tzinfo:
        end_dt = end_dt.astimezone(timezone.utc).replace(tzinfo=None)

    total_revenue = 0.0
    kitchen_revenue = 0.0
    hot_revenue = 0.0
    deliveries_count = 0

    if emp and is_cook_employee(emp):
        # 1. Повар: выручка по цехам "Кухня" и "Горячий цех"
        kitchen_zone_ids, hot_zone_ids = get_cook_kitchen_zones(session)

        orders = session.exec(
            select(Order)
            .where(
                Order.status.in_([OrderStatus.closed, OrderStatus.delivered]),
                Order.created_at >= start_dt,
                Order.created_at <= end_dt
            )
        ).all()

        k_sum = 0.0
        h_sum = 0.0

        for o in orders:
            items = session.exec(select(OrderItem).where(OrderItem.order_id == o.id)).all()
            # Пропорция скидки заказа
            ratio = (
                float(o.total_with_discount) / float(o.total_amount)
                if (o.total_amount and float(o.total_amount) > 0)
                else 1.0
            )
            for it in items:
                kz = it.kitchen_zone_id
                if not kz and it.product_id:
                    p = session.get(Product, it.product_id)
                    if p:
                        kz = p.kitchen_zone_id
                if not kz and it.product_name:
                    p = session.exec(select(Product).where(Product.name == it.product_name)).first()
                    if p:
                        kz = p.kitchen_zone_id

                sub = float(it.total) * ratio
                if kz in kitchen_zone_ids:
                    k_sum += sub
                elif kz in hot_zone_ids:
                    h_sum += sub

        kitchen_revenue = round(k_sum, 2)
        hot_revenue = round(h_sum, 2)
        total_revenue = round(k_sum + h_sum, 2)

    elif emp and is_courier_employee(emp):
        # 2. Курьер: выручка по доставкам
        orders_revenue = session.exec(
            select(func.sum(Order.total_with_discount))
            .where(
                Order.courier_name == emp.name,
                Order.status.in_([OrderStatus.closed, OrderStatus.delivered]),
                Order.created_at >= start_dt,
                Order.created_at <= end_dt
            )
        ).first()

        del_count = session.exec(
            select(func.count(Order.id))
            .where(
                Order.courier_name == emp.name,
                Order.status.in_([OrderStatus.closed, OrderStatus.delivered]),
                Order.created_at >= start_dt,
                Order.created_at <= end_dt
            )
        ).one()

        total_revenue = round(float(orders_revenue or 0.0), 2)
        deliveries_count = int(del_count or 0)

    else:
        # 3. Администратор / Кассир / Прочий персонал
        admin_revenue = None
        if emp and emp.name:
            admin_revenue = session.exec(
                select(func.sum(Order.total_with_discount))
                .where(
                    Order.admin_name == emp.name,
                    Order.status.in_([OrderStatus.closed, OrderStatus.delivered]),
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt
                )
            ).first()

        if admin_revenue is not None and float(admin_revenue) > 0:
            total_revenue = round(float(admin_revenue), 2)
        else:
            # Общая выручка заведения за время смены
            gen_rev = session.exec(
                select(func.sum(Order.total_with_discount))
                .where(
                    Order.status.in_([OrderStatus.closed, OrderStatus.delivered]),
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt
                )
            ).first()
            total_revenue = round(float(gen_rev or 0.0), 2)

    # 4. Количество отмененных заказов за период смены
    cancelled_count = session.exec(
        select(func.count(Order.id))
        .where(
            Order.status == OrderStatus.cancelled,
            Order.created_at >= start_dt,
            Order.created_at <= end_dt
        )
    ).one()

    return {
        "total_revenue": total_revenue,
        "kitchen_revenue": kitchen_revenue,
        "hot_revenue": hot_revenue,
        "deliveries_count": deliveries_count,
        "cancelled_count": int(cancelled_count or 0)
    }
