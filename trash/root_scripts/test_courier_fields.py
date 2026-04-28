#!/usr/bin/env python3
"""Финальный тест - находим все нужные поля курьера и доставки"""
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

        good_filter = {
            "OpenDate.Typed": {
                "filterType": "DateRange", "periodType": "CUSTOM",
                "from": "2026-04-01", "to": "2026-04-19",
                "includeLow": True, "includeHigh": False
            }
        }

        print("=== DELIVERIES - поиск полей курьера и доставки ===")
        courier_candidates = [
            "WaiterName", "DeliveryDriver", "CourierName", "Deliveryman",
            "DeliveryEmployeeName", "Driver", "DriverName",
            "DeliveryZone", "DeliveryArea", "Zone",
            "DeliveryAddress", "AddressStreet", "AddressHouse",
            "DeliveryTime", "ActualDelivery", "ExpectedDelivery",
            "DeliveryDelay", "DelayTime", "LateMinutes",
            "DeliveryDuration", "CookingTime",
            "OrderType", "OrderSource", "OrderChannel",
            "OrderCreateTime", "OrderCloseTime",
        ]

        working_fields = []
        for field in courier_candidates:
            payload = {
                "reportType": "DELIVERIES",
                "groupByRowFields": ["OrderNum", field],
                "aggregateFields": ["DishDiscountSumInt"],
                "filters": good_filter
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                rows = d.get('data', [])
                print(f"✅ '{field}' => {len(rows)} rows | Sample: {rows[0] if rows else '{}'}")
                working_fields.append(field)
            else:
                err = r3.text.replace('java.lang.IllegalArgumentException: ','').replace('\n','')[:50]
                if 'Unknown OLAP field' not in err:
                    print(f"⚠️  '{field}' => {err}")

        print(f"\n=== Рабочие поля: {working_fields} ===")

        # Теперь полный запрос с реальными данными доставок
        print("\n=== Полный запрос доставок с рабочими полями ===")
        all_fields = ["OrderNum", "OpenTime", "CloseTime", "WaiterName"] + [f for f in working_fields if f not in ["OrderNum", "OpenTime", "CloseTime", "WaiterName"]]
        payload_full = {
            "reportType": "DELIVERIES",
            "groupByRowFields": all_fields[:8],  # max 8 полей
            "aggregateFields": ["DishDiscountSumInt"],
            "filters": good_filter
        }
        r_full = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload_full)
        if r_full.status_code == 200:
            d_full = r_full.json()
            print(f"✅ Полный запрос: {len(d_full.get('data',[]))} rows")
            for row in d_full.get('data', [])[:5]:
                print(f"  {row}")
        else:
            print(f"❌ {r_full.text[:200]}")

asyncio.run(main())
