"""
API эндпоинты для OLAP-отчётов по выручке из iiko
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import datetime, date, timedelta
from app.core.datetime_utils import utc_now
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.iiko_settings import IikoSettings
from app.models.olap_revenue import OlapRevenueRecord
from app.services.iiko_service import iiko_service
from app.services.revenue_sync import revenue_sync_service


router = APIRouter(prefix="/reports", tags=["Reports"])


def _get_period_dates(period: str, date_from_str: Optional[str], date_to_str: Optional[str]):
    """Возвращает (date_from, date_to) datetime в UTC для указанного периода"""
    now = utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

    if period == "today":
        return today_start, today_end
    elif period == "yesterday":
        yesterday = today_start - timedelta(days=1)
        return yesterday, yesterday.replace(hour=23, minute=59, second=59)
    elif period == "week":
        return today_start - timedelta(days=7), today_end
    elif period == "month":
        return today_start - timedelta(days=30), today_end
    elif period == "year":
        return today_start - timedelta(days=365), today_end
    elif period == "custom":
        if not date_from_str or not date_to_str:
            raise HTTPException(status_code=400, detail="date_from and date_to are required for custom period")
        try:
            df = datetime.fromisoformat(date_from_str).replace(tzinfo=utc_now().tzinfo)
            dt = datetime.fromisoformat(date_to_str).replace(tzinfo=utc_now().tzinfo)
            return df, dt
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601: YYYY-MM-DDTHH:MM:SS")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown period: {period}. Use: today, yesterday, week, month, year, custom")


@router.get("/olap/revenue")
async def get_revenue_report(
    period: str = Query(default="today", description="Период: today, yesterday, week, month, year, custom"),
    date_from: Optional[str] = Query(default=None, description="Начало для custom периода (ISO 8601)"),
    date_to: Optional[str] = Query(default=None, description="Конец для custom периода (ISO 8601)"),
    include_deleted: bool = Query(default=False, description="Включать удалённые заказы"),
    refresh: bool = Query(default=False, description="Принудительно обновить данные из iiko"),
    db: Session = Depends(get_session),
):
    """
    Получение OLAP-данных по выручке.
    - Для текущего дня (today) — всегда запрашивает живые данные из iiko.
    - Для остальных периодов — ищет в БД. Если нет или refresh=True, запрашивает iiko.
    """
    date_from_dt, date_to_dt = _get_period_dates(period, date_from, date_to)
    is_today = (period == "today")

    # Для прошлых периодов проверяем кэш в БД
    if not is_today and not refresh:
        cached = db.exec(
            select(OlapRevenueRecord).where(
                OlapRevenueRecord.date_from >= date_from_dt,
                OlapRevenueRecord.date_to <= date_to_dt,
                OlapRevenueRecord.period_type == period,
                OlapRevenueRecord.include_deleted == include_deleted,
            )
        ).all()
        if cached:
            return {
                "success": True,
                "period": period,
                "date_from": date_from_dt.isoformat(),
                "date_to": date_to_dt.isoformat(),
                "source": "database",
                "data": [_record_to_dict(r) for r in cached],
            }

    # Получаем настройки iiko
    settings = db.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=400, detail="iiko settings not configured")

    try:
        rows = await iiko_service.get_olap_report(
            date_from=date_from_dt,
            date_to=date_to_dt,
            api_login=settings.api_login,
            organization_id=settings.organization_id,
            include_deleted=include_deleted,
            resto_url=settings.resto_url,
            resto_login=settings.resto_login,
            resto_password=settings.resto_password,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"iiko API error: {str(e)}")

    # Сохраняем в БД (только для не текущего дня)
    if not is_today and rows:
        # Удаляем старые записи за этот период
        old_records = db.exec(
            select(OlapRevenueRecord).where(
                OlapRevenueRecord.period_type == period,
                OlapRevenueRecord.date_from >= date_from_dt,
                OlapRevenueRecord.date_to <= date_to_dt,
                OlapRevenueRecord.include_deleted == include_deleted,
            )
        ).all()
        for old in old_records:
            db.delete(old)
        db.commit()

        # Сохраняем новые
        for row in rows:
            record = OlapRevenueRecord(
                organization_id=settings.organization_id,
                organization_name=row.get("department", settings.organization_id),
                terminal_name=row.get("terminal", ""),
                date_from=date_from_dt,
                date_to=date_to_dt,
                business_date=row.get("date"),
                period_type=period,
                average_check=row.get("average_check", 0.0),
                markup=row.get("markup", 0.0),
                markup_percent=row.get("markup_percent", 0.0),
                cost_price=row.get("cost_price", 0.0),
                cost_price_percent=row.get("cost_price_percent", 0.0),
                discount_sum=row.get("discount_sum", 0.0),
                revenue=row.get("revenue", 0.0),
                orders_count=row.get("orders_count", 0),
                include_deleted=include_deleted,
                updated_at=utc_now(),
            )
            db.add(record)
        db.commit()

    return {
        "success": True,
        "period": period,
        "date_from": date_from_dt.isoformat(),
        "date_to": date_to_dt.isoformat(),
        "source": "iiko_live" if is_today else "iiko_refreshed",
        "data": rows,
    }


@router.post("/olap/sync")
async def sync_revenue(
    period: str = Query(default="today", description="Период для синхронизации: today, yesterday")
):
    """
    Принудительный запуск синхронизации выручки из iiko.
    """
    try:
        await revenue_sync_service.sync_period(period)
        return {"success": True, "message": f"Синхронизация выручки за {period} запущена и завершена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при синхронизации: {str(e)}")


@router.get("/olap/sales")
async def get_sales_report(
    period: str = Query(default="today"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    refresh: bool = Query(default=False),
    db: Session = Depends(get_session),
):
    df, dt = _get_period_dates(period, date_from, date_to)
    settings = db.exec(select(IikoSettings)).first()
    rows = await iiko_service.get_custom_olap_report(
        "SALES",
        ["Department", "OpenDate.Typed"],
        ["fullSum", "DiscountSum", "UniqOrderId", "GuestNum"],
        df, dt, settings.organization_id
    )
    return {"success": True, "data": rows}

@router.get("/olap/products")
async def get_products_report(
    period: str = Query(default="today"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    refresh: bool = Query(default=False),
    db: Session = Depends(get_session),
):
    df, dt = _get_period_dates(period, date_from, date_to)
    settings = db.exec(select(IikoSettings)).first()
    rows = await iiko_service.get_custom_olap_report(
        "SALES",
        ["DishName", "DishCategory"],
        ["DishAmountInt", "DishDiscountSumInt", "UniqOrderId"],
        df, dt, settings.organization_id
    )
    return {"success": True, "data": rows}

@router.get("/olap/days")
async def get_days_report(
    period: str = Query(default="today"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    refresh: bool = Query(default=False),
    db: Session = Depends(get_session),
):
    df, dt = _get_period_dates(period, date_from, date_to)
    settings = db.exec(select(IikoSettings)).first()
    rows = await iiko_service.get_custom_olap_report(
        "SALES",
        ["OpenDate.Typed"],
        ["fullSum", "UniqOrderId"],
        df, dt, settings.organization_id
    )
    return {"success": True, "data": rows}

@router.get("/olap/clients")
async def get_clients_report(
    period: str = Query(default="today"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    refresh: bool = Query(default=False),
    db: Session = Depends(get_session),
):
    df, dt = _get_period_dates(period, date_from, date_to)
    settings = db.exec(select(IikoSettings)).first()
    rows = await iiko_service.get_custom_olap_report(
        "SALES",
        ["Customer.Name", "Customer.Phone"],
        ["fullSum", "UniqOrderId"],
        df, dt, settings.organization_id
    )
    return {"success": True, "data": rows}

@router.get("/olap/orders")
async def get_orders_olap_report(
    period: str = Query(default="today"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    refresh: bool = Query(default=False),
    db: Session = Depends(get_session),
):
    df, dt = _get_period_dates(period, date_from, date_to)
    settings = db.exec(select(IikoSettings)).first()
    rows = await iiko_service.get_custom_olap_report(
        "SALES",
        ["OrderNum", "OpenTime", "Customer.Name", "Delivery.Courier"],
        ["fullSum", "UniqOrderId"],
        df, dt, settings.organization_id
    )
    return {"success": True, "data": rows}

@router.get("/olap/payments")
async def get_payments_report(
    period: str = Query(default="today"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    refresh: bool = Query(default=False),
    db: Session = Depends(get_session),
):
    df, dt = _get_period_dates(period, date_from, date_to)
    settings = db.exec(select(IikoSettings)).first()
    rows = await iiko_service.get_custom_olap_report(
        "SALES",
        ["PayTypes"],
        ["fullSum", "UniqOrderId"],
        df, dt, settings.organization_id
    )
    return {"success": True, "data": rows}

def _record_to_dict(r: OlapRevenueRecord) -> dict:
    return {
        "organization_id": r.organization_id,
        "organization_name": r.organization_name,
        "terminal_name": r.terminal_name,
        "business_date": r.business_date,
        "average_check": r.average_check,
        "markup": r.markup,
        "markup_percent": r.markup_percent,
        "cost_price": r.cost_price,
        "cost_price_percent": r.cost_price_percent,
        "discount_sum": r.discount_sum,
        "revenue": r.revenue,
        "orders_count": r.orders_count,
        "cash_sum": r.cash_sum or 0.0,
        "card_sum": r.card_sum or 0.0,
        "online_sum": r.online_sum or 0.0,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }
