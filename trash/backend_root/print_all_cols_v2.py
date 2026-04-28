import asyncio
import hashlib
import httpx
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings

async def get_all_metadata():
    with Session(engine) as session:
        s = session.exec(select(IikoSettings)).first()
        url, login, password = s.resto_url, s.resto_login, s.resto_password
        
    base_url = "https://dovezzuka-tyumen.iiko.it/resto/api"
    pwd_hash = hashlib.sha1(password.encode()).hexdigest()
    
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.get(f"{base_url}/auth", params={"login": login, "pass": pwd_hash})
        token = r.text.strip().strip('"')
        
        ep = f"{base_url}/v2/reports/olap/columns/DELIVERIES"
        r2 = await client.get(ep, params={"key": token})
        if r2.status_code == 200:
            cols = r2.json()
            for c in cols:
                print(c)
        else:
            print(f"Failed: {r2.status_code} at {ep}")

if __name__ == "__main__":
    asyncio.run(get_all_metadata())
