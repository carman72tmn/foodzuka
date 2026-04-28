#!/usr/bin/env python3
"""Тест доступных полей OLAP и исправление синхронизации"""
import asyncio, sys
sys.path.insert(0, '/app')
import logging
logging.basicConfig(level=logging.WARNING)

async def main():
    from app.core.database import SessionLocal
    from app.services.iiko_service import iiko_service
    from sqlmodel import select
    from app.models import IikoSettings
    import httpx, hashlib

    with SessionLocal() as session:
        from sqlmodel import select
        settings_db = session.exec(select(IikoSettings)).first()
        url = settings_db.resto_url
        login = settings_db.resto_login
        password = settings_db.resto_password

    base_url = url.rstrip('/')
    if base_url.endswith('/resto'):
        base_url = f"{base_url}/api"
    elif not base_url.endswith('/api'):
        base_url = f"{base_url}/resto/api"

    pwd_hash = hashlib.sha1(password.encode()).hexdigest()

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        # Auth
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        token = r.text.strip().strip('"')
        print(f"Auth token: {token[:20]}...")

        # Тест 1: Узнаем доступные поля DELIVERIES
        print("\n=== TEST DELIVERIES fields ===")
        payload = {
            "reportType": "DELIVERIES",
            "groupByRowFields": ["OrderNum"],
            "aggregateFields": ["OrderSum"],
            "filters": {
                "ActualDeliveryTime": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": "2026-04-15T00:00:00.000",
                    "to": "2026-04-19T00:00:00.000",
                    "includeLow": True,
                    "includeHigh": False
                }
            }
        }
        r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
        print(f"Status: {r2.status_code}")
        if r2.status_code == 200:
            data = r2.json()
            print(f"Columns: {data.get('columnNames', [])}")
            rows = data.get('data', [])
            print(f"Rows count: {len(rows)}")
            if rows:
                print(f"First row: {rows[0]}")
        else:
            print(f"Error: {r2.text}")

        # Тест 2: Попробуем поля курьера
        print("\n=== TEST with CourierName field ===")
        for courier_field in ["CourierName", "Courier", "Employee.Name", "Deliveryman"]:
            payload2 = {
                "reportType": "DELIVERIES",
                "groupByRowFields": ["OrderNum", courier_field],
                "aggregateFields": ["OrderSum"],
                "filters": {
                    "ActualDeliveryTime": {
                        "filterType": "DateRange",
                        "periodType": "CUSTOM",
                        "from": "2026-04-17T00:00:00.000",
                        "to": "2026-04-19T00:00:00.000",
                        "includeLow": True,
                        "includeHigh": False
                    }
                }
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload2)
            if r3.status_code == 200:
                d = r3.json()
                print(f"  '{courier_field}' => OK! Rows: {len(d.get('data', []))}, Cols: {d.get('columnNames', [])}")
            else:
                print(f"  '{courier_field}' => {r3.status_code}: {r3.text[:100]}")

        # Тест 3: Смены SALES
        print("\n=== TEST SALES shifts ===")
        payload3 = {
            "reportType": "SALES",
            "groupByRowFields": ["Employee.Id", "Session.Id", "OpenTime", "CloseTime"],
            "aggregateFields": ["DishDiscountSumInt"],
            "filters": {
                "OpenTime": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": "2026-04-01T00:00:00.000",
                    "to": "2026-04-19T00:00:00.000",
                    "includeLow": True,
                    "includeHigh": False
                }
            }
        }
        r4 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload3)
        print(f"Status: {r4.status_code}")
        if r4.status_code == 200:
            d4 = r4.json()
            print(f"Columns: {d4.get('columnNames', [])}")
            rows4 = d4.get('data', [])
            print(f"Rows: {len(rows4)}")
            if rows4:
                print(f"First: {rows4[0]}")
        else:
            print(f"Error: {r4.text}")

asyncio.run(main())
