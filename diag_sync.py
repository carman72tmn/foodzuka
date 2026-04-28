#!/usr/bin/env python3
"""Диагностика синхронизации сотрудников"""
import asyncio
import sys
sys.path.insert(0, '/app')

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(name)s: %(message)s')

async def main():
    from app.core.database import SessionLocal
    from app.services.iiko_sync_service import iiko_sync_service
    from app.services.iiko_service import iiko_service
    from sqlmodel import select
    from app.models import IikoSettings

    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        print(f"Resto URL: {settings.resto_url}")
        print(f"Resto login: {settings.resto_login}")
        print(f"Resto password set: {bool(settings.resto_password)}")
        print()

        # Тест 1: Получение сотрудников
        print("=== STEP 1: get_resto_employees ===")
        try:
            employees = await iiko_service.get_resto_employees()
            print(f"OK: Получено {len(employees)} сотрудников")
            if employees:
                print(f"  Пример: {employees[0].get('name')} / {employees[0].get('role')}")
        except Exception as e:
            print(f"ERROR: {e}")

        # Тест 2: OLAP смены
        print()
        print("=== STEP 2: get_olap_shift_stats_resto ===")
        from datetime import datetime, timedelta, timezone
        import zoneinfo
        tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
        now = datetime.now(tz)
        date_from = now - timedelta(days=14)
        try:
            shifts = await iiko_service.get_olap_shift_stats_resto(date_from, now)
            print(f"OK: Получено {len(shifts)} смен из OLAP")
            if shifts:
                print(f"  Поля: {list(shifts[0].keys())}")
                print(f"  Пример: {shifts[0]}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

        # Тест 3: Детальные доставки
        print()
        print("=== STEP 3: get_resto_detailed_deliveries ===")
        try:
            deliveries = await iiko_service.get_resto_detailed_deliveries(
                date_from=date_from,
                date_to=now,
                organization_id=settings.organization_id or "",
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            print(f"OK: Получено {len(deliveries)} доставок")
            if deliveries:
                print(f"  Поля: {list(deliveries[0].keys())[:10]}")
        except AttributeError as e:
            print(f"AttributeError (метод не существует): {e}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

asyncio.run(main())
