from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.core.datetime_utils import get_tz, get_local_now, get_day_boundaries
from datetime import datetime, timezone, timedelta

with Session(engine) as db:
    # Имитируем запрос от суперпользователя
    current_user = db.exec(select(User).where(User.username == "0001")).first()
    print("User is_superuser:", current_user.is_superuser)
    
    # 1. include_closed = True
    query = select(Order).where(Order.order_type == "Доставка")
    query = query.where(Order.status.in_([OrderStatus.closed, OrderStatus.cancelled, OrderStatus.delivered]))
    
    # Сверим, сколько заказов на этом этапе
    orders = db.exec(query).all()
    print("Stage 1 (type=Доставка, status=closed/cancelled/delivered):", len(orders))
    
    # 2. Фильтрация по умолчанию (только за сегодня)
    tz_name = str(get_tz(db))
    now_local = get_local_now(tz_name)
    df_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    df_utc = df_local.astimezone(timezone.utc).replace(tzinfo=None)
    
    query2 = query.where(Order.created_at >= df_utc)
    orders2 = db.exec(query2).all()
    print(f"Stage 2 (created_at >= {df_utc}):", len(orders2))
    for o in orders2:
        print(f"Order #{o.id}: created_at={o.created_at}, status={o.status}, courier={o.courier_name}")
