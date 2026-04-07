import asyncio
import httpx
import hashlib
import json
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings

async def find_columns():
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        
    password_sha1 = hashlib.sha1(settings.resto_password.encode()).hexdigest()
    base_url = settings.resto_url.rstrip('/') + "/api"
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        auth = await client.get(f"{base_url}/auth", params={"login": settings.resto_login, "pass": password_sha1})
        token = auth.text.strip().replace('"', '')
        
        resp = await client.get(f"{base_url}/v2/reports/olap/columns", params={"key": token, "reportType": "SALES"})
        if resp.status_code == 200:
            data = resp.json()
            print("--- AGGREGATE FIELDS ---")
            for k, v in data.items():
                if v.get("aggregationAllowed"):
                    name = str(v.get('name', '')).lower()
                    if 'выруч' in name or 'скидк' in name or 'сумм' in name or 'кол' in name or 'гост' in name or 'чек' in name:
                        print(f"{k} : {v.get('name')}")
        else:
            print("Error", resp.text)

if __name__ == "__main__":
    asyncio.run(find_columns())
