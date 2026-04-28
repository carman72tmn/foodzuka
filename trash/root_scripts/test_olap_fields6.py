#!/usr/bin/env python3
"""Тест правильного формата OpenDate фильтра для iiko Resto OLAP"""
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

        # Правильный фильтр OpenDate
        filter_formats = [
            {"OpenDate.Date": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-16", "to": "2026-04-19", "includeLow": True, "includeHigh": False}},
            {"OpenDate": {"filterType": "DateRange", "periodType": "YESTERDAY", "from": "2026-04-16", "to": "2026-04-19", "includeLow": True, "includeHigh": False}},
            {"OpenDate": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-16T00:00:00.000", "to": "2026-04-19T00:00:00.000", "includeLow": True, "includeHigh": False}},
        ]

        print("=== Correct OpenDate filter formats ===")
        for flt in filter_formats:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["DishName"],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": flt
            }
            r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            fname = list(flt.keys())[0]
            if r2.status_code == 200:
                d = r2.json()
                print(f"✅ {fname} periodType={flt[fname].get('periodType')} => {len(d.get('data',[]))} rows, cols={d.get('columnNames',[])} ")
                if d.get('data'):
                    print(f"   Sample: {d['data'][0]}")
            else:
                print(f"❌ {fname} => {r2.text[:100]}")

        # После того как нашли рабочий фильтр - тестируем поля сотрудников
        print("\n=== Employee fields with correct filter ===")
        good_filter = {"OpenDate.Date": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-01", "to": "2026-04-19", "includeLow": True, "includeHigh": False}}

        employee_field_candidates = [
            "Employee.Id", "EmployeeId", "WaiterId", "CashierId",
            "Employee.Name", "WaiterName", "CashierName",
            "Session.Id", "PersonalSessionId", "CashSessionId",
            "PersonalSession.Id", "PersonalSession.OpenTime",
            "PersonalSession.CloseTime",
        ]
        for ef in employee_field_candidates:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": [ef],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": good_filter
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                print(f"  ✅ '{ef}' => {len(d.get('data',[]))} rows, cols={d.get('columnNames',[])} ")
                if d.get('data'):
                    print(f"     Sample: {d['data'][0]}")
            else:
                err = r3.text.replace('java.lang.IllegalArgumentException: ','').replace('\n','')[:60]
                print(f"  ❌ '{ef}' => {err}")

asyncio.run(main())
