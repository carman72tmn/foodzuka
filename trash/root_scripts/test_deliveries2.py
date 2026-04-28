#!/usr/bin/env python3
"""Поиск рабочих полей для DELIVERIES reportType"""
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

        # Поиск aggregate полей для DELIVERIES
        print("=== DELIVERIES - поиск правильных aggregate полей ===")
        for agg_field in ["DishDiscountSumInt", "OrderSumWithDiscount", "TotalSum", "Sum", 
                          "ActualDeliveryTime", "ExpectedDeliveryTime", "DeliveryOrderSum",
                          "DeliverySum", "Revenue"]:
            payload = {
                "reportType": "DELIVERIES",
                "groupByRowFields": ["OrderNum"],
                "aggregateFields": [agg_field],
                "filters": good_filter_sales
            }
            r2 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r2.status_code == 200:
                d = r2.json()
                print(f"✅ agg='{agg_field}' => {len(d.get('data',[]))} rows")
                if d.get('data'):
                    print(f"   Sample: {d['data'][0]}")
                break
            else:
                err = r2.text.replace('java.lang.IllegalArgumentException: ','').replace('\n','')[:60]
                print(f"❌ agg='{agg_field}' => {err}")

        # Попробуем DELIVERIES без aggregate полей  
        print("\n=== DELIVERIES - только groupBy без aggregate ===")
        payload_no_agg = {
            "reportType": "DELIVERIES",
            "groupByRowFields": ["OrderNum"],
            "aggregateFields": [],
            "filters": good_filter_sales
        }
        r_no = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload_no_agg)
        print(f"Status: {r_no.status_code} | {r_no.text[:200]}")

        # Попробуем другой фильтр для DELIVERIES
        print("\n=== DELIVERIES - разные обязательные фильтры ===")
        for filter_name in ["OpenDate.Typed", "CloseDate.Typed", "ActualDeliveryDate.Typed",
                            "CreateDate.Typed", "DeliveryDate.Typed", "SendDate.Typed",
                            "DeliveryCloseDate.Typed", "ActualDeliveryDateTime.Typed"]:
            payload = {
                "reportType": "DELIVERIES",
                "groupByRowFields": ["OrderNum"],
                "aggregateFields": [],
                "filters": {filter_name: {"filterType": "DateRange", "periodType": "CUSTOM", "from": "2026-04-01", "to": "2026-04-19", "includeLow": True, "includeHigh": False}}
            }
            r3 = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
            if r3.status_code == 200:
                d = r3.json()
                print(f"✅ DELIVERIES filter='{filter_name}' => {len(d.get('data',[]))} rows")
                if d.get('data'):
                    print(f"   Sample: {d['data'][0]}")
                break
            else:
                err = r3.text.replace('\n','')[:100]
                if 'необходимых фильтров' in err:
                    # Извлечём имя правильного фильтра из ошибки
                    print(f"⚠️  '{filter_name}' => {err}")
                    break
                elif 'Unknown OLAP field' in err:
                    print(f"❌ filter='{filter_name}' => UNKNOWN")
                else:
                    print(f"? filter='{filter_name}' => {err[:80]}")

        # Используем реальные заказы из нашей БД для сопоставления
        print("\n=== Получаем заказы из нашей БД для проверки ===")
        from app.core.database import SessionLocal
        from app.models import Order
        from sqlmodel import select
        with SessionLocal() as sess:
            orders = sess.exec(select(Order).where(Order.order_type == 'Доставка').limit(5)).all()
            print(f"Заказы на доставку в нашей БД: {len(orders)}")
            for o in orders:
                print(f"  iiko_order_id={o.iiko_order_id}, courier_name={o.courier_name}, zone={o.delivery_zone}, delay={o.delay_minutes}")

asyncio.run(main())
