
import asyncio
import sys
import os
import httpx
import hashlib
import json
from sqlmodel import Session, create_engine, select
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.iiko_settings import IikoSettings

engine = create_engine(settings.DATABASE_URL)

async def main():
    with Session(engine) as session:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            print("Settings not found")
            return
            
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
        # Auth
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        token = r.text.strip().strip('"')

        # Test query
        payload = {
            "reportType": "DELIVERIES",
            "groupByRowFields": [
                "Delivery.Number",
                "Delivery.Address",
                "Delivery.City",
                "Delivery.Street"
            ],
            "aggregateFields": ["fullSum"],
            "filters": {
                "Delivery.ActualTime": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT00:00:00.000"),
                    "to": datetime.now().strftime("%Y-%m-%dT23:59:59.000"),
                    "includeLow": True,
                    "includeHigh": True
                }
            }
        }
        r = await client.post(f"{base_url}/v2/reports/olap", params={"key": token}, json=payload)
        if r.status_code == 200:
            data = r.json()
            print(f"Columns: {data.get('columnNames')}")
            rows = data.get('data', [])
            print(f"Fetched {len(rows)} rows.")
            if rows:
                print(f"Sample row: {rows[0]}")
        else:
            print(f"Error: {r.status_code} {r.text}")

if __name__ == "__main__":
    asyncio.run(main())
