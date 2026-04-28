#!/usr/bin/env python3
"""Финальный тест OLAP - пробуем /reports/olap (без v2) и правильный OpenDate"""
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

        # Тест: /reports/olap (500 раньше, но вдруг с данными работает)
        print("=== /reports/olap с правильным форматом ===")
        payload_old = {
            "reportType": "SALES",
            "groupByRowFields": ["DishName"],
            "aggregateFields": ["DishDiscountSumInt"],
            "filters": {
                "OpenDate": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "dateFrom": "2026-04-16",
                    "dateTo": "2026-04-19"
                }
            }
        }
        r_old = await client.post(f"{base_url}/reports/olap", params={"key": token}, json=payload_old)
        print(f"/reports/olap: {r_old.status_code} | {r_old.text[:200]}")

        # Пробуем формат без /v2
        for ep in ["/reports/olap", "/olap/report"]:
            for payload_test in [
                {"reportType": "SALES", "from": "2026-04-16", "to": "2026-04-19"},
                {"type": "SALES", "from": "2026-04-16", "to": "2026-04-19"},
            ]:
                r2 = await client.post(f"{base_url}{ep}", params={"key": token}, json=payload_test)
                print(f"POST {ep}: {r2.status_code} | {r2.text[:100]}")

        # Самый важный тест: используем /v2/reports/olap с ПРАВИЛЬНЫМ фильтром OpenDate
        # Из ошибки видно что система ожидает фильтр именно "OpenDate" 
        # но в формате от/до через запятую или другой структуре
        print("\n=== v2 OLAP с разными структурами фильтра OpenDate ===")
        filter_structs = [
            {"OpenDate": {"filterType": "DateRange", "from": "2026-04-16", "to": "2026-04-19"}},
            {"OpenDate": {"filterType": "DateRange", "greaterOrEqual": "2026-04-16", "lessOrEqual": "2026-04-19"}},
            {"OpenDate": {"from": "2026-04-16", "to": "2026-04-19"}},
            {"OpenDate": {"gte": "2026-04-16", "lte": "2026-04-19"}},
        ]
        for flt in filter_structs:
            payload = {"reportType": "SALES", "groupByRowFields": ["DishName"], "aggregateFields": ["DishDiscountSumInt"], "filters": flt}
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                print(f"  ✅ {list(flt['OpenDate'].keys())} => {len(d.get('data',[]))} rows, cols={d.get('columnNames',[])} ")
            else:
                err = r3.text.replace('\n','')[:80]
                print(f"  ❌ {list(flt['OpenDate'].keys())} => {err}")

        # Проверяем XML формат /reports/olap
        print("\n=== XML формат для /reports/olap ===")
        xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
<olapRequest reportType="SALES">
  <dimensions>
    <dimension name="DishName"/>
  </dimensions>
  <measures>
    <measure name="DishDiscountSumInt"/>
  </measures>
  <filters>
    <filter field="OpenDate">
      <filterType>DateRange</filterType>
      <from>2026-04-16</from>
      <to>2026-04-19</to>
    </filter>
  </filters>
</olapRequest>"""
        r_xml = await client.post(
            f"{base_url}/reports/olap",
            params={"key": token},
            content=xml_payload.encode('utf-8'),
            headers={"Content-Type": "application/xml"}
        )
        print(f"XML POST /reports/olap: {r_xml.status_code} | {r_xml.text[:200]}")

asyncio.run(main())
