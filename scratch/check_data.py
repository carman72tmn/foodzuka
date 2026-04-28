import asyncio
import sys
from datetime import datetime, timezone, timedelta
sys.path.insert(0, '/app')

async def main():
    from app.services.iiko_sync_service import iiko_sync_service
    from app.core.database import SessionLocal
    from app.models import CourierOrder, Employee, Shift
    from sqlalchemy import select, func
    import zoneinfo
    
    with SessionLocal() as session:
        print("--- Проверка данных за 2026-04-24 ---")
        
        # 1. Проверка сотрудника 369
        emp = session.get(Employee, 369)
        if emp:
            print(f"Сотрудник 369: Name={emp.name}, IikoID={emp.iiko_id}")
        else:
            print("Сотрудник 369 не найден!")
            
        # 2. Проверка заказов за сегодня
        today = datetime(2026, 4, 24)
        stmt = select(func.count(CourierOrder.id)).where(CourierOrder.created_at_iiko >= today)
        count = session.exec(stmt).first()
        print(f"Всего заказов в courier_orders за сегодня: {count}")
        
        # 3. Проверка заказов для сотрудника 369
        stmt = select(func.count(CourierOrder.id)).where(
            CourierOrder.created_at_iiko >= today,
            CourierOrder.employee_id == 369
        )
        emp_count = session.exec(stmt).first()
        print(f"Заказов для сотрудника 369 за сегодня (created_at_iiko): {emp_count}")
        
        # 4. Проверка фильтрации по actual_delivery_time (как в API)
        # API использует UTC фильтр.
        # Если сегодня 2026-04-24 19:00 local (UTC+5), то df_utc = 2026-04-24 00:00 local = 2026-04-23 19:00 UTC
        # и dt_utc = 2026-04-24 23:59 local = 2026-04-24 18:59 UTC
        
        df_utc = datetime(2026, 4, 23, 19, 0, tzinfo=timezone.utc)
        dt_utc = datetime(2026, 4, 24, 18, 59, 59, tzinfo=timezone.utc)
        
        stmt = select(func.count(CourierOrder.id)).where(
            CourierOrder.actual_delivery_time >= df_utc,
            CourierOrder.actual_delivery_time <= dt_utc
        )
        # ВАЖНО: Если actual_delivery_time в базе НАИВНЫЙ, то сравнение с TZ-aware может вернуть 0
        print(f"Фильтр по actual_delivery_time (TZ-aware): {session.exec(stmt).first()}")
        
        # Попробуем наивный фильтр (предположим база хранит как UTC или Local без TZ)
        df_naive = datetime(2026, 4, 23, 19, 0)
        dt_naive = datetime(2026, 4, 24, 18, 59, 59)
        stmt = select(func.count(CourierOrder.id)).where(
            CourierOrder.actual_delivery_time >= df_naive,
            CourierOrder.actual_delivery_time <= dt_naive
        )
        print(f"Фильтр по actual_delivery_time (Naive): {session.exec(stmt).first()}")

        # Проверим пример значения в базе
        stmt = select(CourierOrder).where(CourierOrder.created_at_iiko >= today).limit(1)
        first_order = session.exec(stmt).first()
        if first_order:
            print(f"Пример заказа {first_order.order_num}: actual_delivery_time={first_order.actual_delivery_time}, type={type(first_order.actual_delivery_time)}")

if __name__ == "__main__":
    asyncio.run(main())
