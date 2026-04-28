
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
        print(f"Authenticating to {base_url} as {login}...")
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        if r.status_code != 200:
            print(f"Auth failed: {r.status_code} {r.text}")
            return
            
        token = r.text.strip().strip('"')
        print(f"Auth successful, token: {token[:10]}...")

        # Get available columns
        print("\n=== Available OLAP Columns for DELIVERIES ===")
        cols_url = f"{base_url}/v2/reports/olap/columns"
        r = await client.get(cols_url, params={"key": token, "reportType": "DELIVERIES"})
        if r.status_code != 200:
            print(f"Failed to get columns: {r.status_code} {r.text}")
            return
            
        cols = r.json()
        
        # Look for address-related columns
        print("Address-related columns found:")
        found = False
        for c in cols:
            cid = c.get("id", "")
            if any(x in cid for x in ["Address", "Street", "House", "Flat", "Entrance", "Floor", "Doorphone", "City", "Region"]):
                print(f"  {cid} ({c.get('name')})")
                found = True
        
        if not found:
            print("No address-related columns found by keywords. Printing all columns...")
            for c in cols:
                print(f"  {c.get('id')} ({c.get('name')})")

if __name__ == "__main__":
    asyncio.run(main())
