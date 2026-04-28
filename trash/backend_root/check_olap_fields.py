import asyncio
import httpx
import hashlib
from sqlmodel import Session, select
import sys

# Add backend to path to import models and core
sys.path.append('.')

from app.core.database import engine
from app.models.iiko_settings import IikoSettings

async def check_olap():
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        
    password_sha1 = hashlib.sha1(settings.resto_password.encode()).hexdigest()
    base_url = settings.resto_url.rstrip('/') + "/api"
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        auth = await client.get(f"{base_url}/auth", params={"login": settings.resto_login, "pass": password_sha1})
        token = auth.text.strip().replace('"', '')
        
        resp = await client.get(f"{base_url}/v2/reports/olap/columns", params={"key": token, "reportType": "SALES"})
        data = resp.json()
        
        # Look for our target fields
        targets = ["OrderSum", "DiscountSum", "UniqOrderCount", "GuestNum", "DishAmount", "DishSum", "DishDiscountSum", "UniqOrderId"]
        found = []
        for key in data.keys():
            if any(t.lower() in key.lower() for t in targets):
                found.append(f"{key}: {data[key].get('name')}")
        
        print("FOUND COLUMNS:")
        for f in sorted(found):
            print(f)

if __name__ == "__main__":
    asyncio.run(check_olap())
