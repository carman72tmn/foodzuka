#!/usr/bin/env python3
"""Тест различных OLAP reportType и минимальных запросов"""
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

        # Попробуем разные reportType со списком полей из официальной документации
        tests = [
            ("SALES with Employee.Name", "SALES", ["Employee.Name"], ["DishDiscountSumInt"]),
            ("SALES with EmployeeName", "SALES", ["EmployeeName"], ["DishDiscountSumInt"]),
            ("SALES with CashRegisterSession.Id", "SALES", ["CashRegisterSession.Id"], ["DishDiscountSumInt"]),
            ("SALES with SessionId", "SALES", ["SessionId"], ["DishDiscountSumInt"]),
            ("SALES with SessionNum", "SALES", ["SessionNum"], ["DishDiscountSumInt"]),
            ("SALES with CashGroupSessionNum", "SALES", ["CashGroupSessionNum"], ["DishDiscountSumInt"]),
        ]

        for name, rtype, group, aggr in tests:
            payload = {
                "reportType": rtype,
                "groupByRowFields": group,
                "aggregateFields": aggr,
                "filters": {
                    "OpenDate": {
                        "filterType": "DateRange",
                        "periodType": "CUSTOM",
                        "from": "2026-04-16T00:00:00.000",
                        "to": "2026-04-19T00:00:00.000",
                        "includeLow": True,
                        "includeHigh": False
                    }
                }
            }
            r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r2.status_code == 200:
                d = r2.json()
                rows = d.get('data', [])
                cols = d.get('columnNames', [])
                print(f"✅ {name} => {len(rows)} rows, cols={cols}")
                if rows:
                    print(f"   Sample: {rows[0]}")
            else:
                err = r2.text.replace('java.lang.IllegalArgumentException: ', '')[:80]
                print(f"❌ {name} => {err}")

        # Пробуем совсем минимальный запрос чтобы понять форматы
        print("\n=== Minimal SALES - no filters ===")
        payload_min = {
            "reportType": "SALES",
            "groupByRowFields": ["DishName"],
            "aggregateFields": ["DishAmount"],
        }
        r_min = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload_min)
        if r_min.status_code == 200:
            d_min = r_min.json()
            print(f"  OK! Cols: {d_min.get('columnNames', [])} | Rows: {len(d_min.get('data', []))}")
        else:
            print(f"  {r_min.text[:200]}")

        # Пробуем XML OLAP (старый формат)
        print("\n=== XML OLAP endpoint ===")
        r_xml = await client.get(f"{base_url}/v2/entities/Employee", params={"key": token})
        print(f"  /v2/entities/Employee: {r_xml.status_code} | {r_xml.text[:200]}")

        r_emp = await client.get(f"{base_url}/employees", params={"key": token})
        print(f"  /employees: {r_emp.status_code} | {r_emp.text[:300]}")

asyncio.run(main())
