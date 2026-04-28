#!/usr/bin/env python3
"""Тест OpenDate.Typed - правильный фильтр для iiko Resto OLAP"""
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

        # Правильный фильтр: OpenDate.Typed
        print("=== TEST OpenDate.Typed filter ===")
        filter_variants = [
            {"OpenDate.Typed": {"filterType": "DateRange", "periodType": "TODAY"}},
            {"OpenDate.Typed": {"filterType": "DateRange", "periodType": "YESTERDAY"}},
            {"OpenDate.Typed": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-01", "to": "2026-04-19", "includeLow": True, "includeHigh": False}},
        ]
        for flt in filter_variants:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["DishName"],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": flt
            }
            r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            fkey = list(flt.keys())[0]
            pt = flt[fkey].get('periodType', 'CUSTOM')
            if r2.status_code == 200:
                d = r2.json()
                print(f"✅ {fkey} periodType={pt} => {len(d.get('data',[]))} rows, cols={d.get('columnNames',[])} ")
                if d.get('data'):
                    print(f"   Sample: {d['data'][0]}")
            else:
                err = r2.text.replace('\n','')[:100]
                print(f"❌ {fkey} periodType={pt} => {err}")

        # Теперь тестируем поля сотрудников с правильным фильтром
        print("\n=== Employee/Session fields with OpenDate.Typed ===")
        good_filter = {"OpenDate.Typed": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-01", "to": "2026-04-19", "includeLow": True, "includeHigh": False}}

        field_candidates = [
            "DishName", "OrderNum", "WaiterName", "WaiterId",
            "Employee.Id", "Employee.Name", "EmployeeCode",
            "SessionNum", "SessionDate", "CloseSessionSaleSum",
            "PersonalSessionNum", "PersonalSessionOpenTime",
            "CloseTime", "OpenTime", "DishDiscountSumInt",
            "UniqOrderId", "TableNum", "TableName",
            "StoreId", "StoreName", "Department",
            "PayTypes", "DayOfWeek",
        ]

        for field in field_candidates:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": [field],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": good_filter
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                rows = d.get('data', [])
                print(f"  ✅ '{field}' => {len(rows)} rows")
                if rows:
                    print(f"     cols={d.get('columnNames',[])} | Sample: {rows[0]}")
            else:
                err = r3.text.replace('java.lang.IllegalArgumentException: ','').replace('\n','')[:50]
                if 'Unknown OLAP field' in err:
                    print(f"  ❌ '{field}' => UNKNOWN")
                else:
                    print(f"  ⚠️  '{field}' => {err}")

asyncio.run(main())
