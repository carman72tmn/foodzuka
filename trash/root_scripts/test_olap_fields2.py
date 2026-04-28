#!/usr/bin/env python3
"""Получение доступных OLAP полей через iiko Resto API"""
import asyncio, sys, json
sys.path.insert(0, '/app')
import logging
logging.basicConfig(level=logging.WARNING)
import httpx, hashlib

async def main():
    from app.core.database import SessionLocal
    from sqlmodel import select
    from app.models import IikoSettings

    with SessionLocal() as session:
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
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        token = r.text.strip().strip('"')
        print(f"Token: {token[:20]}...\n")

        # Получаем список доступных полей для DELIVERIES
        print("=== GET OLAP FIELDS for DELIVERIES ===")
        r2 = await client.get(f"{base_url}/v2/reports/olap/columns/DELIVERIES", params={"key": token})
        print(f"Status: {r2.status_code}")
        if r2.status_code == 200:
            try:
                fields = r2.json()
                print(f"Fields count: {len(fields)}")
                for f in fields[:50]:
                    if isinstance(f, dict):
                        print(f"  {f.get('name', f)}")
                    else:
                        print(f"  {f}")
            except:
                print(f"Raw: {r2.text[:1000]}")
        else:
            print(f"Error: {r2.text[:500]}")

        # Получаем список доступных полей для SALES
        print("\n=== GET OLAP FIELDS for SALES ===")
        r3 = await client.get(f"{base_url}/v2/reports/olap/columns/SALES", params={"key": token})
        print(f"Status: {r3.status_code}")
        if r3.status_code == 200:
            try:
                fields3 = r3.json()
                print(f"Fields count: {len(fields3)}")
                for f in fields3[:80]:
                    if isinstance(f, dict):
                        n = f.get('name', '')
                        t = f.get('type', '')
                        print(f"  [{t}] {n}")
                    else:
                        print(f"  {f}")
            except:
                print(f"Raw: {r3.text[:2000]}")
        else:
            print(f"Error: {r3.text[:500]}")

        # Также пробуем старый v1 OLAP
        print("\n=== TEST OLD /api/v1/reports/olap ===")
        r4 = await client.post(f"{base_url}/v1/reports/olap", params={"key": token}, json={
            "reportType": "SALES",
            "dimensions": [{"name": "Employee.Id"}],
            "measures": [{"name": "DishDiscountSumInt"}],
            "filters": {}
        })
        print(f"v1 Status: {r4.status_code} | {r4.text[:200]}")

asyncio.run(main())
