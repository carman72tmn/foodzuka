import asyncio
import hashlib
import httpx
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings

async def get_metadata():
    with Session(engine) as session:
        s = session.exec(select(IikoSettings)).first()
        url, login, password = s.resto_url, s.resto_login, s.resto_password
        
    base_url = url.rstrip('/')
    if base_url.endswith('/resto'): base_url = f"{base_url}/api"
    elif not base_url.endswith('/api'): base_url = f"{base_url}/resto/api"
        
    pwd_hash = hashlib.sha1(password.encode()).hexdigest()
    
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        token = r.text.strip().strip('"')
        
        # Пробуем разные варианты получения колонок
        endpoints = [
            f"{base_url}/v2/reports/olap/columns/DELIVERIES",
            f"{base_url}/v2/reports/olap/columns?reportType=DELIVERIES",
            f"{base_url}/v1/reports/olap/columns?reportType=DELIVERIES"
        ]
        
        for ep in endpoints:
            print(f"Testing {ep}...")
            r2 = await client.get(ep, params={"key": token})
            if r2.status_code == 200:
                print(f"✅ Success! Columns:")
                cols = r2.json()
                for c in cols:
                    name = c.get('name') if isinstance(c, dict) else c
                    if "Courier" in str(name) or "Driver" in str(name) or "Delivery" in str(name) or "Zone" in str(name):
                        print(f"  - {c}")
            else:
                print(f"❌ Failed: {r2.status_code}")

if __name__ == "__main__":
    asyncio.run(get_metadata())
