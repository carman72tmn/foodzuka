#!/usr/bin/env python3
"""Тест DELIVERIES reportType с правильным фильтром"""
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

        good_filter_sales = {
            "OpenDate.Typed": {
                "filterType": "DateRange", "periodType": "CUSTOM",
                "from": "2026-04-01", "to": "2026-04-19",
                "includeLow": True, "includeHigh": False
            }
        }

        # Сначала найдём правильный фильтр для DELIVERIES
        print("=== DELIVERIES reportType - ищем обязательный фильтр ===")
        delivery_filter_candidates = [
            {"OpenDate.Typed": good_filter_sales["OpenDate.Typed"]},
            {"CloseDate.Typed": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-01", "to": "2026-04-19", "includeLow": True, "includeHigh": False}},
            {"ActualDeliveryDate.Typed": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-01", "to": "2026-04-19", "includeLow": True, "includeHigh": False}},
            {"OrderDate.Typed": {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-01", "to": "2026-04-19", "includeLow": True, "includeHigh": False}},
        ]
        for flt in delivery_filter_candidates:
            payload = {
                "reportType": "DELIVERIES",
                "groupByRowFields": ["OrderNum"],
                "aggregateFields": ["OrderSum"],
                "filters": flt
            }
            r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            fname = list(flt.keys())[0]
            if r2.status_code == 200:
                d = r2.json()
                print(f"✅ DELIVERIES filter={fname} => {len(d.get('data',[]))} rows")
                if d.get('data'):
                    print(f"   Sample: {d['data'][0]}")
                    break
            else:
                err = r2.text.replace('\n','')[:90]
                print(f"❌ DELIVERIES filter={fname} => {err}")

        # Тест Employee/Waiter полей для смен
        print("\n=== Ищем поля для идентификации сотрудника и смены ===")
        field_candidates_2 = [
            "WaiterCode", "WaiterSurname", "WaiterMiddleName",
            "CashierName", "CashierCode", 
            "PersonalCashierName", "PersonalCashier",
            "PersonalSession.OpenDate", "PersonalSession.CloseDate",
            "CashSessionOpenDate", "CashSessionCloseDate",
            "CashSessionDate", "CashSessionOpenTime", "CashSessionCloseTime",
            "PersonalSessionOpenDate", "PersonalSessionCloseDate",
        ]

        for field in field_candidates_2:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": [field],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": good_filter_sales
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                rows = d.get('data', [])
                print(f"  ✅ '{field}' => {len(rows)} rows | Sample: {rows[0] if rows else '{}'}")
            else:
                err = r3.text.replace('java.lang.IllegalArgumentException: ','').replace('\n','')[:50]
                if 'Unknown OLAP field' in err:
                    pass  # skip unknown
                else:
                    print(f"  ⚠️  '{field}' => {err}")

        # Работает SessionNum - попробуем получить имя сотрудника через отдельный запрос
        print("\n=== Получаем данные по сессиям через SessionNum + WaiterName ===")
        payload_session = {
            "reportType": "SALES",
            "groupByRowFields": ["SessionNum", "WaiterName", "OpenTime", "CloseTime"],
            "aggregateFields": ["DishDiscountSumInt"],
            "filters": good_filter_sales
        }
        r_sess = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload_session)
        if r_sess.status_code == 200:
            d_sess = r_sess.json()
            print(f"✅ Session+Waiter => {len(d_sess.get('data',[]))} rows")
            for row in d_sess.get('data', [])[:10]:
                print(f"  {row}")
        else:
            print(f"❌ {r_sess.text[:200]}")

asyncio.run(main())
