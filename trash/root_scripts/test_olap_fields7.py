#!/usr/bin/env python3
"""Исследование доступных endpoints iiko Resto"""
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
        print(f"Token OK: {token[:15]}...\n")

        # Тестируем доступные v1 endpoints
        endpoints = [
            ("GET", "/olap", None),
            ("GET", "/reports/olap", None),
            ("GET", "/v1/reports/olap", None),
            ("GET", "/v1/employees/personalSessions", {"dateFrom": "2026-04-16", "dateTo": "2026-04-19"}),
            ("GET", "/employees/personalSessions", {"dateFrom": "2026-04-16", "dateTo": "2026-04-19"}),
            ("GET", "/v2/employees/personalSessions", {"dateFrom": "2026-04-16", "dateTo": "2026-04-19"}),
            ("GET", "/sessions", None),
            ("GET", "/v1/sessions", None),
            ("GET", "/v2/sessions", None),
            ("GET", "/shifts", None),
            ("GET", "/personnelactions", None),
            ("GET", "/personnelaction", None),
            ("GET", "/timeclock", None),
            ("GET", "/staffschedule", None),
        ]

        for method, ep, params in endpoints:
            req_params = {"key": token}
            if params:
                req_params.update(params)
            try:
                r2 = await client.request(method, f"{base_url}{ep}", params=req_params, timeout=5)
                if r2.status_code == 200:
                    sample = r2.text[:150].replace('\n', ' ')
                    print(f"✅ {method} {ep} => 200 | {sample}")
                elif r2.status_code != 404:
                    print(f"⚠️  {method} {ep} => {r2.status_code} | {r2.text[:80]}")
                else:
                    print(f"❌ {method} {ep} => 404")
            except Exception as e:
                print(f"💥 {method} {ep} => {e}")

        # Ищем правильный фильтр для OLAP
        print("\n=== OLAP correct filter name ===")
        filter_names = ["AccountingDate", "AccountDate", "SaleDate", "TransactionDate", "DishDate", "OrderCloseDate", "BusinessDate", "RecordDate"]
        for fn in filter_names:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["DishName"],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": {fn: {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-16", "to": "2026-04-19", "includeLow": True, "includeHigh": False}}
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                print(f"✅ filter='{fn}' => {len(d.get('data',[]))} rows")
            else:
                err = r3.text.replace('java.lang.IllegalArgumentException: ','').replace('\n','')[:80]
                if 'необходимых фильтров' not in err:
                    print(f"❌ filter='{fn}' => {err}")
                else:
                    print(f"⚠️  filter='{fn}' => REQUIRED FILTER MISSING (тот же)")

asyncio.run(main())
