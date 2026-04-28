from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from typing import List, Optional
import zoneinfo

from app.core.database import get_session, engine
from app.models.employee import Employee, Shift, Schedule, CourierOrder
from app.services.iiko_sync_service import iiko_sync_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

from app.core.datetime_utils import get_tz_name, to_local, get_local_now

def _get_tz_name(session: Session) -> str:
    return get_tz_name(session)

def _to_local(dt: Optional[datetime], session: Session) -> Optional[datetime]:
    if dt is None:
        return None
    tz_name = _get_tz_name(session)
    return to_local(dt, tz_name)

def _fmt_time(dt: Optional[datetime], session: Session) -> Optional[str]:
    if dt is None:
        return None
    local_dt = _to_local(dt, session)
    return local_dt.strftime("%H:%M") if local_dt else None

def _fmt_dt(dt: Optional[datetime], session: Session) -> Optional[str]:
    if dt is None:
        return None
    local_dt = _to_local(dt, session)
    return local_dt.isoformat() if local_dt else None


def _is_courier(emp: Employee) -> bool:
    role = (emp.role or "").lower()
    name = (emp.name or "").lower()
    return ("курьер" in role or "courier" in role or role in ["cur", "cour"]
            or "курьер" in name or "courier" in name)


def _is_admin(emp: Employee) -> bool:
    role = (emp.role or "").lower()
    name = (emp.name or "").lower()
    return any(k in role for k in ["администратор", "оператор", "manager", "старший", "adm", "admin"])


# ---------------------------------------------------------------------------
# Синхронизация
# ---------------------------------------------------------------------------

@router.post("/sync/full")
async def sync_employees_and_deliveries_full(
    days: int = 14,
    session: Session = Depends(get_session)
):
    """Принудительная синхронизация сотрудников и доставок курьеров"""
    try:
        # Синхронизируем сотрудников (профили + явки)
        await iiko_sync_service.sync_employees_full(session, days=days)
        # Синхронизируем детальные доставки из OLAP
        await iiko_sync_service.sync_courier_deliveries(session, days=days)
        return {"success": True, "message": "Синхронизация сотрудников и доставок завершена"}
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Список сотрудников
# ---------------------------------------------------------------------------

@router.get("/")
@router.get("")
def get_employees(
    status: Optional[str] = None,
    role: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Получение списка сотрудников"""
    query = select(Employee)
    if status is not None:
        query = query.where(Employee.status == status)
    if role is not None:
        query = query.where(Employee.role == role)

    employees = session.exec(query.order_by(Employee.name)).all()
    result = []
    for e in employees:
        d = e.model_dump()
        d["is_courier"] = _is_courier(e)
        d["is_admin"] = _is_admin(e)
        result.append(d)
    return {"status": "success", "data": result}


# ---------------------------------------------------------------------------
# Смены конкретного сотрудника
# ---------------------------------------------------------------------------

@router.get("/{employee_id}/shifts")
def get_employee_shifts(employee_id: int, session: Session = Depends(get_session)):
    employee = session.exec(select(Employee).where(Employee.id == employee_id)).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    shifts = session.exec(
        select(Shift).where(Shift.employee_id == employee_id).order_by(Shift.date_open.desc())
    ).all()
    return {"status": "success", "data": shifts}


@router.get("/{employee_id}/stats")
async def get_employee_stats(
    employee_id: int,
    mode: str = "calendar",
    session: Session = Depends(get_session)
):
    """Статистика сотрудника (calendar = текущая неделя, sliding = 7 дней)"""
    stats = await iiko_sync_service.get_employee_stats(session, employee_id, mode)
    return {"status": "success", "data": stats}


# ---------------------------------------------------------------------------
# Открытые смены (дашборд)
# ---------------------------------------------------------------------------

@router.get("/shifts/open")
def get_open_shifts(session: Session = Depends(get_session)):
    shifts = session.exec(select(Shift).where(Shift.status == "OPEN").order_by(Shift.date_open.desc())).all()
    result = []
    for s in shifts:
        d = s.model_dump()
        d["employee_name"] = s.employee.name if s.employee else "Unknown"
        result.append(d)
    return {"status": "success", "data": result}


@router.get("/shifts/open/detailed")
def get_open_shifts_detailed(session: Session = Depends(get_session)):
    """Для дашборда: кто сейчас на смене"""
    from sqlalchemy.orm import selectinload
    shifts = session.exec(
        select(Shift)
        .options(selectinload(Shift.employee))
        .where(Shift.status == "OPEN")
        .order_by(Shift.date_open.desc())
    ).all()

    result = []
    for shift in shifts:
        open_local = _to_local(shift.date_open, session)
        elapsed_minutes = int((datetime.now(timezone.utc) - (shift.date_open if shift.date_open.tzinfo else shift.date_open.replace(tzinfo=timezone.utc))).total_seconds() / 60)
        result.append({
            "id": shift.id,
            "employee_id": shift.employee_id,
            "employee_name": shift.employee.name if shift.employee else "Unknown",
            "employee_role": shift.employee.role if shift.employee else None,
            "shift_start": open_local.strftime("%H:%M") if open_local else "—",
            "shift_date": open_local.strftime("%d.%m.%Y") if open_local else "—",
            "elapsed_minutes": elapsed_minutes,
            "elapsed_text": f"{elapsed_minutes // 60}ч {elapsed_minutes % 60}м",
        })
    return {"status": "success", "data": result}


# ---------------------------------------------------------------------------
# Все смены с фильтрами
# ---------------------------------------------------------------------------

@router.get("/shifts/all")
def get_all_shifts(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    tz_name = get_tz_name(session)
    query = select(Shift).order_by(Shift.date_open.desc())

    if date_from:
        try:
            df = datetime.fromisoformat(date_from).replace(tzinfo=zoneinfo.ZoneInfo(tz_name))
            query = query.where(Shift.date_open >= df.astimezone(timezone.utc))
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to).replace(tzinfo=zoneinfo.ZoneInfo(tz_name), hour=23, minute=59, second=59)
            query = query.where(Shift.date_open <= dt.astimezone(timezone.utc))
        except Exception:
            pass
    if status:
        query = query.where(Shift.status == status.upper())
    if employee_id:
        query = query.where(Shift.employee_id == employee_id)

    shifts = session.exec(query).all()
    result = []
    for shift in shifts:
        open_local = _to_local(shift.date_open, session)
        close_local = _to_local(shift.date_close, session)
        result.append({
            "id": shift.id,
            "iiko_id": shift.iiko_id,
            "employee_id": shift.employee_id,
            "employee_name": shift.employee.name if shift.employee else "Unknown",
            "employee_role": shift.employee.role if shift.employee else None,
            "date": open_local.strftime("%d.%m.%Y") if open_local else "—",
            "date_iso": open_local.date().isoformat() if open_local else None,
            "day_of_week": day_names[open_local.weekday()] if open_local else "—",
            "time_open": open_local.strftime("%H:%M") if open_local else "—",
            "time_open_full": open_local.isoformat() if open_local else None,
            "time_close": close_local.strftime("%H:%M") if close_local else None,
            "time_close_full": close_local.isoformat() if close_local else None,
            "status": shift.status,
            "work_hours": round(shift.work_hours or 0.0, 2),
            "revenue_at_close": shift.revenue_at_close or 0.0,
            "cancelled_orders_count": shift.cancelled_orders_count or 0,
            "deliveries_count": shift.deliveries_count or 0,
            "employee_rate": shift.employee.rate if shift.employee else None,
        })
    return {"status": "success", "data": result, "total": len(result)}


# ---------------------------------------------------------------------------
# Расписания
# ---------------------------------------------------------------------------

@router.get("/schedules")
def get_schedules(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    query = select(Schedule)
    if date_from:
        query = query.where(Schedule.date_from >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(Schedule.date_to <= datetime.fromisoformat(date_to))

    schedules = session.exec(query.order_by(Schedule.date_from.asc())).all()
    result = []
    for sc in schedules:
        d = sc.model_dump()
        d["employee_name"] = sc.employee.name if sc.employee else "Unknown"
        result.append(d)
    return {"status": "success", "data": result}


# ---------------------------------------------------------------------------
# Синхронизация
# ---------------------------------------------------------------------------

@router.post("/sync")
def sync_employees_bg(background_tasks: BackgroundTasks, days: int = 14):
    """Запуск фоновой синхронизации сотрудников, смен и доставок"""
    async def run_sync():
        try:
            with Session(engine) as sync_session:
                await iiko_sync_service.sync_employees_full(sync_session, days=days)
                await iiko_sync_service.sync_courier_deliveries(sync_session, days=days)
                logger.info("Background employee + courier delivery sync completed")
        except Exception as e:
            logger.error(f"Fatal error in background employee sync: {e}")

    background_tasks.add_task(run_sync)
    return {"status": "success", "message": f"Синхронизация сотрудников запущена (за {days} дней)"}


@router.post("/sync/couriers")
def sync_couriers_bg(background_tasks: BackgroundTasks, days: int = 7):
    """Запуск фоновой синхронизации только доставок курьеров"""
    async def run_sync():
        try:
            with Session(engine) as sync_session:
                await iiko_sync_service.sync_courier_deliveries(sync_session, days=days)
                logger.info(f"Background courier delivery sync completed for {days} days")
        except Exception as e:
            logger.error(f"Fatal error in background courier sync: {e}")

    background_tasks.add_task(run_sync)
    return {"status": "success", "message": f"Синхронизация доставок запущена (за {days} дней)"}


# ---------------------------------------------------------------------------
# НОВЫЙ: Детальный отчёт по курьерам
# ---------------------------------------------------------------------------

@router.get("/reports/courier-detail")
def get_courier_detail_report(
    background_tasks: BackgroundTasks,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Детальный отчёт по курьерам за период.
    Источник данных: таблица courier_orders (OLAP данные).
    """
    from app.models import CourierOrder, Employee, IikoSettings
    settings = session.exec(select(IikoSettings)).first()
    city_name = settings.city_name if settings else "Тюмень"
    addr_fmt = (settings.address_format or "components") if settings else "components"

    tz_name = get_tz_name(session)
    now_local = get_local_now(tz_name)
    df_local = datetime.fromisoformat(date_from).replace(tzinfo=zoneinfo.ZoneInfo(tz_name)) if date_from else now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    if date_to:
        # Если передана только дата (YYYY-MM-DD), fromisoformat поставит 00:00:00.
        # Нам нужно 23:59:59, чтобы захватить весь день.
        dt_local = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=zoneinfo.ZoneInfo(tz_name))
    else:
        dt_local = now_local.replace(hour=23, minute=59, second=59)

    # Если запрос включает сегодняшний день — запускаем фоновую синхронизацию для актуализации данных
    if dt_local.date() >= now_local.date():
        async def run_sync_bg():
            with Session(engine) as sync_session:
                await iiko_sync_service.sync_courier_deliveries(sync_session, days=1)
        background_tasks.add_task(run_sync_bg)

    df_utc = df_local.astimezone(timezone.utc)
    dt_utc = dt_local.astimezone(timezone.utc)

    # 1. Сначала находим всех курьеров, у которых были смены в этот период
    shift_stmt = select(Shift.employee_id).where(
        Shift.date_open >= df_utc,
        Shift.date_open <= dt_utc
    )
    couriers_with_shifts_ids = set(session.exec(shift_stmt).all())

    # 2. Загружаем все OLAP-записи доставок за период
    # Используем actual_delivery_time для фильтрации
    stmt = select(CourierOrder, Employee).join(Employee).where(
        CourierOrder.actual_delivery_time >= df_utc,
        CourierOrder.actual_delivery_time <= dt_utc
    )
    
    # Фильтруем: только те курьеры, у которых были смены (если смены есть в базе)
    if couriers_with_shifts_ids:
        stmt = stmt.where(CourierOrder.employee_id.in_(list(couriers_with_shifts_ids)))
    
    stmt = stmt.order_by(CourierOrder.actual_delivery_time)
    
    rows = session.exec(stmt).all()

    # Группируем по курьеру
    couriers_map: dict = {}
    for co, emp in rows:
        cname = emp.name
        if cname not in couriers_map:
            couriers_map[cname] = {"name": cname, "orders": []}
        couriers_map[cname]["orders"].append(co)

    result = []
    for cname, cdata in couriers_map.items():
        days_map: dict = {}
        total_revenue = 0.0
        late_count = 0

        for order in cdata["orders"]:
            ref_dt = _to_local(order.actual_delivery_time, session)
            day_key = ref_dt.date().isoformat() if ref_dt else "unknown"

            if day_key not in days_map:
                days_map[day_key] = {
                    "date": day_key,
                    "deliveries_count": 0,
                    "revenue": 0.0,
                    "zones": {},
                    "deliveries": []
                }

            rev = float(order.amount or 0)
            total_revenue += rev
            zone = order.delivery_zone or "Не указана"
            is_late = order.is_late or False
            if is_late:
                late_count += 1

            days_map[day_key]["deliveries_count"] += 1
            days_map[day_key]["revenue"] += rev
            days_map[day_key]["zones"][zone] = days_map[day_key]["zones"].get(zone, 0) + 1
            
            # Детализация заказа
            days_map[day_key]["deliveries"].append({
                "order_num": order.order_num,
                "iiko_id": order.iiko_id,
                "address": iiko_sync_service.format_address(order.address_parts, city=city_name, fmt=addr_fmt) if order.address_parts else (order.address or ""),
                "zone": zone,
                "amount": rev,
                "expected_time": _fmt_dt(order.expected_delivery_time, session),
                "actual_time": _fmt_dt(order.actual_delivery_time, session),
                "delay_minutes": order.delay_minutes,
                "is_late": is_late,
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "description": order.items_summary or ""
            })

        zones_summary: dict = {}
        for d in days_map.values():
            for z, c in d["zones"].items():
                zones_summary[z] = zones_summary.get(z, 0) + c

        result.append({
            "courier_name": cname,
            "total_deliveries": len(cdata["orders"]),
            "total_revenue": round(total_revenue, 2),
            "late_count": late_count,
            "zones_summary": zones_summary,
            "days": sorted(days_map.values(), key=lambda x: x["date"], reverse=True)
        })

    return {"status": "success", "data": result}


# ---------------------------------------------------------------------------
# НОВЫЙ: Отчёт по сменам администраторов
# ---------------------------------------------------------------------------

@router.get("/reports/admin-shifts")
def get_admin_shifts_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Отчёт по сменам администраторов:
    Дата, Открытие, Закрытие, Часов, Выручка кассы, Отменённые заказы.
    """
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    tz_name = get_tz_name(session)
    now_local = get_local_now(tz_name)
    df = datetime.fromisoformat(date_from).replace(tzinfo=zoneinfo.ZoneInfo(tz_name)) if date_from else (now_local - timedelta(days=7)).replace(hour=0, minute=0, second=0)
    dt = datetime.fromisoformat(date_to).replace(tzinfo=zoneinfo.ZoneInfo(tz_name)) if date_to else now_local.replace(hour=23, minute=59, second=59)

    df_utc = df.astimezone(timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)

    # Администраторы
    admins = [e for e in session.exec(select(Employee)).all() if _is_admin(e)]
    admin_ids = [e.id for e in admins]
    admin_map = {e.id: e for e in admins}

    if not admin_ids:
        return {"status": "success", "data": []}

    shifts = session.exec(
        select(Shift).where(
            Shift.employee_id.in_(admin_ids),
            Shift.date_open >= df_utc,
            Shift.date_open <= dt_utc
        ).order_by(Shift.date_open.desc())
    ).all()

    result = []
    for s in shifts:
        open_local = _to_local(s.date_open, session)
        close_local = _to_local(s.date_close, session)
        emp = admin_map.get(s.employee_id)
        result.append({
            "shift_id": s.id,
            "employee_id": s.employee_id,
            "employee_name": emp.name if emp else "Unknown",
            "employee_role": emp.role if emp else None,
            "date": open_local.strftime("%d.%m.%Y") if open_local else "—",
            "date_iso": open_local.date().isoformat() if open_local else None,
            "day_of_week": day_names[open_local.weekday()] if open_local else "—",
            "time_open": open_local.strftime("%H:%M") if open_local else "—",
            "time_open_full": open_local.isoformat() if open_local else None,
            "time_close": close_local.strftime("%H:%M") if close_local else None,
            "time_close_full": close_local.isoformat() if close_local else None,
            "status": s.status,
            "work_hours": round(s.work_hours or 0.0, 2),
            "revenue_at_close": s.revenue_at_close or 0.0,
            "cancelled_orders_count": s.cancelled_orders_count or 0,
        })

    return {"status": "success", "data": result, "total": len(result)}


# ---------------------------------------------------------------------------
# НОВЫЙ: Еженедельная календарная сетка
# ---------------------------------------------------------------------------

@router.get("/reports/weekly")
def get_weekly_report(
    week_start: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Еженедельная сетка по сотрудникам.
    week_start — ISO-дата понедельника (напр. 2026-04-14).
    Если не указан — текущая неделя.
    """
    tz_name = get_tz_name(session)
    now_local = get_local_now(tz_name)

    if week_start:
        try:
            ws = datetime.fromisoformat(week_start).replace(tzinfo=zoneinfo.ZoneInfo(tz_name), hour=0, minute=0, second=0, microsecond=0)
        except Exception:
            ws = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        ws = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    we = ws + timedelta(days=7)
    ws_utc = ws.astimezone(timezone.utc)
    we_utc = we.astimezone(timezone.utc)

    day_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    week_dates = [(ws + timedelta(days=i)).date().isoformat() for i in range(7)]

    # Загружаем все смены за неделю
    all_shifts = session.exec(
        select(Shift).where(
            Shift.date_open >= ws_utc,
            Shift.date_open < we_utc
        )
    ).all()

    # Загружаем все доставки курьеров за неделю
    all_deliveries = session.exec(
        select(CourierOrder).where(
            CourierOrder.actual_delivery_time >= ws_utc,
            CourierOrder.actual_delivery_time < we_utc
        )
    ).all()

    # Индексируем по сотруднику → дата
    shifts_by_emp: dict = {}
    for s in all_shifts:
        open_local = _to_local(s.date_open, session)
        day_iso = open_local.date().isoformat() if open_local else "unknown"
        shifts_by_emp.setdefault(s.employee_id, {}).setdefault(day_iso, []).append(s)

    deliveries_by_emp: dict = {}
    for d in all_deliveries:
        ref = d.actual_delivery_time or d.created_at_iiko
        if not ref:
            continue
        ref_local = _to_local(ref, session)
        day_iso = ref_local.date().isoformat() if ref_local else "unknown"
        deliveries_by_emp.setdefault(d.employee_id, {}).setdefault(day_iso, []).append(d)

    # Собираем всех задействованных сотрудников
    emp_ids = set(shifts_by_emp.keys()) | set(deliveries_by_emp.keys())
    employees = session.exec(select(Employee).where(Employee.id.in_(list(emp_ids)))).all() if emp_ids else []

    grid = []
    for emp in sorted(employees, key=lambda e: e.name):
        emp_days = []
        for day_iso in week_dates:
            emp_shifts = shifts_by_emp.get(emp.id, {}).get(day_iso, [])
            emp_dels = deliveries_by_emp.get(emp.id, {}).get(day_iso, [])

            total_hours = round(sum(s.work_hours or 0 for s in emp_shifts), 1)
            total_revenue = round(sum(s.revenue_at_close or 0 for s in emp_shifts), 2)
            del_count = len(emp_dels)
            del_revenue = round(sum(d.amount or 0 for d in emp_dels), 2)

            # Зоны доставок
            zones: dict = {}
            for d in emp_dels:
                z = d.delivery_zone or "—"
                zones[z] = zones.get(z, 0) + 1

            emp_days.append({
                "date": day_iso,
                "worked": len(emp_shifts) > 0 or del_count > 0,
                "shifts_count": len(emp_shifts),
                "work_hours": total_hours,
                "revenue": total_revenue,
                "deliveries_count": del_count,
                "deliveries_revenue": del_revenue,
                "zones": zones,
                "zones_str": ", ".join(f"{z}({c})" for z, c in zones.items()) if zones else "",
            })

        grid.append({
            "employee_id": emp.id,
            "employee_name": emp.name,
            "employee_role": emp.role,
            "is_courier": _is_courier(emp),
            "is_admin": _is_admin(emp),
            "days": emp_days,
            "total_hours": round(sum(d["work_hours"] for d in emp_days), 1),
            "total_deliveries": sum(d["deliveries_count"] for d in emp_days),
            "total_revenue": round(sum(d["revenue"] for d in emp_days), 2),
        })

    return {
        "status": "success",
        "week_start": ws.date().isoformat(),
        "week_end": (we - timedelta(days=1)).date().isoformat(),
        "day_labels": day_labels,
        "week_dates": week_dates,
        "data": grid
    }


# ---------------------------------------------------------------------------
# Старый отчёт по курьерам (обратная совместимость)
# ---------------------------------------------------------------------------

@router.get("/reports/couriers")
def get_courier_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Сводный отчёт по курьерам (Оптимизированный).
    Источник: таблица courier_orders (OLAP данные).
    """
    from app.models import CourierOrder, Employee

    tz_name = get_tz_name(session)
    now_local = get_local_now(tz_name)
    df = datetime.fromisoformat(date_from).replace(tzinfo=zoneinfo.ZoneInfo(tz_name)) if date_from else now_local.replace(hour=0, minute=0, second=0)
    if date_to:
        dt = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=zoneinfo.ZoneInfo(tz_name))
    else:
        dt = now_local.replace(hour=23, minute=59, second=59)

    df_utc = df.astimezone(timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)

    # Все OLAP-заказы-доставки за период
    stmt = select(CourierOrder, Employee).join(Employee).where(
        CourierOrder.actual_delivery_time >= df_utc,
        CourierOrder.actual_delivery_time <= dt_utc
    )
    rows = session.exec(stmt).all()

    # Группируем по курьеру
    couriers_map: dict = {}
    for co, emp in rows:
        cname = emp.name
        if cname not in couriers_map:
            couriers_map[cname] = {"orders": [], "zones": {}}
        couriers_map[cname]["orders"].append(co)
        zone = co.delivery_zone or "Не указана"
        couriers_map[cname]["zones"][zone] = couriers_map[cname]["zones"].get(zone, 0) + 1

    report = []
    for cname, cdata in couriers_map.items():
        c_orders = cdata["orders"]
        report.append({
            "name": cname,
            "deliveries": len(c_orders),
            "revenue": round(sum(float(o.amount or 0) for o in c_orders), 2),
            "late_deliveries": sum(1 for o in c_orders if (o.delay_minutes or 0) > 0),
            "zones": cdata["zones"]
        })

    return {"status": "success", "data": report}

