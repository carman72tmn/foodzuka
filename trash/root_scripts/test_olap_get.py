#!/usr/bin/env python3
"""Полный тест iiko Resto API для получения данных персональных смен и доставок"""
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

        # v2/reports/olap с periodType=YESTERDAY (не требует custom дат)
        print("=== v2 OLAP с periodType=YESTERDAY ===")
        for pt in ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_30_DAYS", "THIS_MONTH", "THIS_WEEK"]:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["DishName"],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": {"OpenDate": {"filterType": "DateRange", "periodType": pt}}
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                print(f"✅ periodType={pt} => {len(d.get('data',[]))} rows, cols={d.get('columnNames',[])} ")
                if d.get('data'):
                    print(f"   Sample: {d['data'][0]}")
                    break
            else:
                err = r3.text.replace('\n','')[:90]
                print(f"❌ periodType={pt} => {err}")

        # GET /reports/olap (версия без v2)
        print("\n=== GET /reports/olap (старый API) ===")
        r_get = await client.get(f"{base_url}/reports/olap", params={
            "key": token,
            "reportType": "SALES",
        })
        print(f"Status: {r_get.status_code} | {r_get.text[:200]}")

        # Пробуем другие варианты OLAP полей включая кириллицу
        print("\n=== Пробуем поля для Sessions через sessionOpenDate ===")
        for fn in ["sessionOpenDate", "openDate", "closeDate", "closeTime", "openTime", "sessionDate"]:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["DishName"],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": {fn: {"filterType": "DateRange", "periodType": "TODAY"}}
            }
            r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r2.status_code == 200:
                print(f"✅ '{fn}' => OK!")
            else:
                err = r2.text.replace('\n','')[:70]
                if 'необходимых' in err:
                    print(f"⚠️  '{fn}' => accepted but missing filter")
                else:
                    print(f"❌ '{fn}' => {err[:60]}")

        # Попробуем с v2 запросом без filters вообще (может быть он не обязателен)
        print("\n=== v2 без filters ===")
        payload_nof = {
            "reportType": "SALES",
            "groupByRowFields": ["DishName"],
            "aggregateFields": ["DishDiscountSumInt"],
        }
        r_nof = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload_nof)
        print(f"No filter: {r_nof.status_code} | {r_nof.text[:150]}")

        # Получаем список смен напрямую через employees API
        print("\n=== GET /employees (список всех) ===")
        r_emp = await client.get(f"{base_url}/employees", params={"key": token})
        print(f"Status: {r_emp.status_code} | {r_emp.text[:400]}")

        # Получаем персональные смены через API
        print("\n=== Расписание через schedule ===")
        r_sched = await client.get(f"{base_url}/employees/schedule", params={
            "key": token,
            "from": "2026-04-01",
            "to": "2026-04-19"
        })
        print(f"Status: {r_sched.status_code} | {r_sched.text[:400]}")

asyncio.run(main())
