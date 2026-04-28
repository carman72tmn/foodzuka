import asyncio
import httpx
import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Any, Optional

# Add backend to path for imports
import sys
sys.path.append('/app')

async def debug_iiko():
    from app.core.database import get_session_sync
    from app.models.iiko_settings import IikoSettings
    from sqlmodel import select

    # 1. Get Settings
    with get_session_sync() as session:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db:
            print("ERROR: Iiko settings not found in DB")
            return
        
        api_login = settings_db.api_login
        org_id = settings_db.organization_id
        
    print(f"API Login: {api_login}")
    print(f"Org ID: {org_id}")

    async with httpx.AsyncClient() as client:
        # 2. Get Token
        token_url = "https://api-ru.iiko.services/api/1/access_token"
        resp = await client.post(token_url, json={"apiLogin": api_login}, timeout=30.0)
        if resp.status_code != 200:
            print(f"ERROR getting token: {resp.text}")
            return
        
        token = resp.json().get('token')
        headers = {"Authorization": f"Bearer {token}"}
        print("Token received successfully")

        # 3. Diagnostic 1: Get Organizations
        print("\n--- Diagnostic 1: Organizations ---")
        orgs_resp = await client.get("https://api-ru.iiko.services/api/1/organizations", headers=headers)
        print(f"Orgs Status: {orgs_resp.status_code}")
        if orgs_resp.status_code == 200:
            orgs = orgs_resp.json().get('organizations', [])
            for o in orgs:
                print(f" - {o.get('name')} (ID: {o.get('id')})")

        # 4. Diagnostic 2: Orders by ID (Verify single order)
        order_id = "fe3e255f-7595-42f6-ac37-86af31e9b009"
        print(f"\n--- Diagnostic 2: Order by ID ({order_id}) ---")
        by_id_url = "https://api-ru.iiko.services/api/1/deliveries/by_id"
        resp = await client.post(by_id_url, json={"organizationId": org_id, "orderIds": [order_id]}, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            orders = data.get('orders', [])
            if orders:
                o_wrapper = orders[0]
                o = o_wrapper.get('order', {})
                print(f"Found order in Iiko.")
                print(f" - creationStatus: {o_wrapper.get('creationStatus')}")
                print(f" - status: {o.get('status')}")
                print(f" - deliveryDate: {o.get('deliveryDate')} (THIS IS WHAT FILTER USES)")
                print(f" - whenCreated: {o.get('whenCreated')}")
                print(f" - whenReceivedByApi: {o.get('whenReceivedByApi')}")
                print(f" - completeBefore: {o.get('completeBefore')}")
            else:
                print("Order not found by ID")

        # 5. Diagnostic 3: Test different filters for List Orders
        print("\n--- Diagnostic 3: List Orders Experiments ---")
        
        # Scenario A: Last 24h (Tyumen Local = UTC+5)
        fmt = '%Y-%m-%d %H:%M:%S.000'
        tyumen_now = datetime.now(timezone.utc) + timedelta(hours=5)
        date_to = tyumen_now.strftime(fmt)
        date_from = (tyumen_now - timedelta(hours=24)).strftime(fmt)
        
        # Scenario B: UTC
        utc_to = datetime.now(timezone.utc).strftime(fmt)
        utc_from = (timezone.utc.now() - timedelta(hours=24)).strftime(fmt) if hasattr(timezone.utc, 'now') else (datetime.now(timezone.utc) - timedelta(hours=24)).strftime(fmt)
        
        # Scenario C: Very broad (Month)
        month_from = datetime.now().strftime('%Y-%m-01 00:00:00.000')

        # Scenario D: Today Business Day (00:00 to 23:59)
        today_start = datetime.now().strftime('%Y-%m-%d 00:00:00.000')
        today_end = datetime.now().strftime('%Y-%m-%d 23:59:59.000')

        scenarios = [
            ("24h Local", {"organizationIds": [org_id], "deliveryDateFrom": date_from, "deliveryDateTo": date_to}),
            ("24h UTC", {"organizationIds": [org_id], "deliveryDateFrom": utc_from, "deliveryDateTo": utc_to}),
            ("Today (00-24)", {"organizationIds": [org_id], "deliveryDateFrom": today_start, "deliveryDateTo": today_end}),
            ("Whole Month", {"organizationIds": [org_id], "deliveryDateFrom": month_from})
        ]

        list_url = "https://api-ru.iiko.services/api/1/deliveries/by_delivery_date_and_status"
        for name, payload in scenarios:
            print(f"\nTesting {name}...")
            print(f"Payload: {payload}")
            try:
                r = await client.post(list_url, json=payload, headers=headers, timeout=60.0)
                print(f"Status: {r.status_code}")
                if r.status_code == 200:
                    orders = r.json().get('orders', [])
                    print(f"Result: {len(orders)} orders found")
                    if orders:
                        print(f" - Sample ID: {orders[0].get('id')}")
                else:
                    print(f"Error: {r.text}")
            except Exception as e:
                print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_iiko())
