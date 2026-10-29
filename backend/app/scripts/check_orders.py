from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order
from app.core.datetime_utils import get_tz, get_local_now, get_day_boundaries
from datetime import datetime, timezone, timedelta

with Session(engine) as db:
    tz_name = str(get_tz(db))
    print("TZ Name:", tz_name)
    now_local = get_local_now(tz_name)
    print("Now Local:", now_local)
    
    # Сверим границы для 2026-06-16
    start_utc, end_utc = get_day_boundaries("2026-06-16", tz_name)
    print("Day boundaries for 2026-06-16 (UTC):", start_utc, "to", end_utc)
    
    # Попробуем сделать запрос
    query = select(Order).where(Order.order_type == "Доставка")
    orders = db.exec(query).all()
    print("Total delivery orders in DB:", len(orders))
    for o in orders:
        print(f"Order #{o.id} ({o.external_number}): created_at={o.created_at} (UTC), courier={o.courier_name}, status={o.status}")
