#!/usr/bin/env python3
import asyncio, sys, json, hashlib, httpx

async def main():
    # Импортируем настройки из приложения
    sys.path.insert(0, '/root/foodzuka/foodtech/backend')
    from app.core.database import SessionLocal
    from app.models import IikoSettings
    from sqlmodel import select

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
        # Auth
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        token = r.text.strip().strip('"')
        print(f"Auth Token: {token[:10]}...")

        # Get Columns
        print("\n--- Available columns for DELIVERIES ---")
        r2 = await client.get(f"{base_url}/v2/reports/olap/columns/DELIVERIES", params={"key": token})
        if r2.status_code == 200:
            cols = r2.json()
            # Фильтруем интересные нам поля
            interesting = ["Delivery", "Order", "Courier", "Address", "Time", "Sum", "Number", "Terminal"]
            for col in cols:
                name = col.get("name", "")
                if any(i.lower() in name.lower() for i in interesting):
                    print(f"  {name} ({col.get('type')})")
        else:
            print(f"Error getting columns: {r2.status_code} {r2.text}")

        # Test request with suspected fields
        print("\n--- Test OLAP Request ---")
        payload = {
            "reportType": "DELIVERIES",
            "groupByRowFields": ["Delivery.Number", "Delivery.Courier", "Delivery.ActualTime"],
            "aggregateFields": ["fullSum"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": "2026-04-10",
                    "to": "2026-04-22",
                    "includeLow": True,
                    "includeHigh": False
                }
            }
        }
        r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
        print(f"Status: {r3.status_code}")
        if r3.status_code == 200:
            data = r3.json()
            print(f"Success! Found {len(data.get('data', []))} rows.")
            if data.get('data'):
                print(f"Sample row: {dict(zip(data.get('columnNames', []), data['data'][0]))}")
        else:
            print(f"Error: {r3.text}")

if __name__ == "__main__":
    asyncio.run(main())
