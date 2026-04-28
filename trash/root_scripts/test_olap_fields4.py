#!/usr/bin/env python3
"""Получение доступных OLAP полей через /api/0/olaps/olapReportFields"""
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

        # Пробуем /0/olaps/olapReportFields
        print("=== /0/olaps/olapReportFields ===")
        base0 = base_url.replace('/api', '')
        for endpoint in [
            f"{base0}/api/0/olaps/olapReportFields?reportType=SALES&key={token}",
            f"{base0}/api/0/olaps/olapPresets?key={token}",
            f"{base_url}/0/olaps/olapReportFields?reportType=SALES&key={token}",
            f"{base0}/resto/api/0/olaps/olapReportFields?reportType=SALES&key={token}",
        ]:
            r2 = await client.get(endpoint)
            print(f"  {r2.status_code}: {endpoint.split('?')[0].split('/resto')[-1]}")
            if r2.status_code == 200:
                try:
                    data = r2.json()
                    print(f"    JSON fields: {json.dumps(data)[:500]}")
                except:
                    print(f"    Text: {r2.text[:500]}")

        # Пробуем разные поля для SALES (популярные в iiko)
        print("\n=== Searching correct field names ===")
        candidates = [
            (["DishName"], ["DishAmountInt"]),
            (["DishName"], ["SaleSum"]),
            (["DishName"], ["DishSumInt"]),
            (["EmployeeName"], ["SaleSum"]),
            (["StoreId"], ["SaleSum"]),
            (["OrderDate.Date"], ["SaleSum"]),
            (["OpenDate.Date"], ["SaleSum"]),
            (["CloseDate.Date"], ["SaleSum"]),
            (["Date"], ["SaleSum"]),
            (["WaiterName"], ["SaleSum"]),
        ]
        for group, aggr in candidates:
            payload = {
                "reportType": "SALES",
                "groupByRowFields": group,
                "aggregateFields": aggr,
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                print(f"  ✅ group={group} aggr={aggr} => {len(d.get('data',[]))} rows, cols={d.get('columnNames',[])} ")
            else:
                err = r3.text.replace('java.lang.IllegalArgumentException: ', '').replace('\n','')[:60]
                print(f"  ❌ group={group} aggr={aggr} => {err}")

asyncio.run(main())
