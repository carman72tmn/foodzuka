#!/usr/bin/env python3
"""Финальный тест - правильный формат запроса к iiko Resto OLAP"""
import asyncio, sys, json
sys.path.insert(0, '/app')
import logging; logging.basicConfig(level=logging.WARNING)
import httpx, hashlib

async def main():
    from app.core.database import SessionLocal
    from sqlmodel import select
    from app.models import IikoSettings

    with SessionLocal() as session:
        s = session.exec(select(IikoSettings)).first()
        url, login, password = s.resto_url, s.resto_login, s.resto_password

    base_url = url.rstrip('/')
    if base_url.endswith('/resto'):
        base_url = f"{base_url}/api"
    elif not base_url.endswith('/api'):
        base_url = f"{base_url}/resto/api"

    pwd_hash = hashlib.sha1(password.encode()).hexdigest()

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        token = r.text.strip().strip('"')

        # Пробуем с правильными фильтрами (по документации - нужен CloseDate или OpenDate)
        filters_to_try = [
            {"DishName": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-16", "to": "2026-04-19", "includeLow": True, "includeHigh": False}},
            {"CloseDate": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-16", "to": "2026-04-19"}},
            {"OpenDate": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-16", "to": "2026-04-19"}},
        ]

        print("=== TEST DishDiscountSumInt with required filters ===")
        for flt in filters_to_try:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["DishName"],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": flt
            }
            r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            filter_name = list(flt.keys())[0]
            if r2.status_code == 200:
                d = r2.json()
                print(f"✅ filter={filter_name} => {len(d.get('data',[]))} rows, cols={d.get('columnNames',[])} ")
                if d.get('data'):
                    print(f"   Sample: {d['data'][0]}")
            else:
                print(f"❌ filter={filter_name} => {r2.text[:100]}")

        # Пробуем с CloseDate - это стандартный фильтр для смен
        print("\n=== TEST shifts with employee + session ===")
        # Попробуем что реально знает система - Session это "кассовая смена"
        for fields in [
            (["CashRegisterName"], ["DishDiscountSumInt"]),
            (["PayType"], ["DishDiscountSumInt"]),
            (["OrderNum"], ["DishDiscountSumInt"]),
            (["TableNum"], ["DishDiscountSumInt"]),
            (["WaiterName"], ["DishDiscountSumInt"]),
        ]:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": fields[0],
                "aggregateFields": fields[1],
                "filters": {
                    "CloseDate": {
                        "filterType": "DateRange",
                        "periodType": "CUSTOM",
                        "from": "2026-04-16",
                        "to": "2026-04-19"
                    }
                }
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                print(f"✅ {fields[0]} => {len(d.get('data',[]))} rows, cols={d.get('columnNames',[])} ")
            else:
                err = r3.text.replace('java.lang.IllegalArgumentException: ','')[:70]
                print(f"❌ {fields[0]} => {err}")

        # Попробуем другой тип отчёта - DELIVERY_STAT
        print("\n=== TEST reportType variants ===")
        for rtype in ["DELIVERY_STAT", "PERSONAL_SESSION", "DELIVERIES_STAT", "SESSION", "SHIFT"]:
            payload = {
                "reportType": rtype,
                "groupByRowFields": ["DishName"],
                "aggregateFields": ["DishDiscountSumInt"],
            }
            r4 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r4.status_code == 200:
                print(f"✅ reportType={rtype} => WORKS!")
            else:
                err = r4.text[:80]
                print(f"❌ reportType={rtype} => {err}")

        # Попробуем personalSessions endpoint
        print("\n=== /personalSessions ===")
        r_ps = await client.get(f"{base_url}/v2/entities/employees/personalSessions", params={
            "key": token,
            "dateFrom": "2026-04-16",
            "dateTo": "2026-04-19"
        })
        print(f"Status: {r_ps.status_code} | {r_ps.text[:300]}")

        r_ps2 = await client.get(f"{base_url}/employees/personalSessions", params={
            "key": token,
            "dateFrom": "2026-04-16",
            "dateTo": "2026-04-19"
        })
        print(f"Status2: {r_ps2.status_code} | {r_ps2.text[:300]}")

asyncio.run(main())
