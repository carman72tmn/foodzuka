
import asyncio
import sys
import os
import httpx
import hashlib
import json
from sqlmodel import Session, create_engine, select

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

        # Get Columns
        r = await client.get(f"{base_url}/v2/reports/olap/columns", params={"key": token, "reportType": "DELIVERIES"})
        if r.status_code == 200:
            resp_data = r.json()
            cols = []
            if isinstance(resp_data, list):
                cols = resp_data
            elif isinstance(resp_data, dict):
                cols = resp_data.get("columns") or resp_data.get("data") or []
            
            ids = [c["id"] for c in cols if isinstance(c, dict)]
            print(json.dumps(ids, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {r.status_code} {r.text}")

if __name__ == "__main__":
    asyncio.run(main())
