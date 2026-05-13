import asyncio
import httpx
import hashlib
import json
from app.core.database import get_session_sync
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def main():
    with get_session_sync() as session:
        res = session.exec(select(IikoSettings)).first()
        if not res:
            return
        
        url = res.resto_url or "https://dovezzuka-tyumen.iiko.it"
        login = res.resto_login
        password = res.resto_password
        
        base_url = url.rstrip('/')
        if not base_url.endswith('/api'):
            if base_url.endswith('/resto'):
                base_url = f"{base_url}/api"
            else:
                base_url = f"{base_url}/resto/api"
        
        async with httpx.AsyncClient(verify=False) as client:
            password_sha1 = hashlib.sha1(password.encode()).hexdigest()
            resp = await client.get(f"{base_url}/auth", params={"login": login, "pass": password_sha1})
            if resp.status_code != 200:
                resp = await client.get(f"{base_url}/auth", params={"login": login, "pass": password})
            
            if resp.status_code != 200:
                return
            
            token = resp.text.strip().replace('"', '')
            
            cols_url = f"{base_url}/v2/reports/olap/columns"
            resp = await client.get(cols_url, params={"key": token, "reportType": "SALES"})
            if resp.status_code == 200:
                cols = resp.json()
                with open("sales_columns.json", "w", encoding="utf-8") as f:
                    json.dump(cols, f, ensure_ascii=False, indent=2)
                print("Saved sales_columns.json")
            
            resp = await client.get(cols_url, params={"key": token, "reportType": "DELIVERIES"})
            if resp.status_code == 200:
                cols = resp.json()
                with open("deliveries_columns.json", "w", encoding="utf-8") as f:
                    json.dump(cols, f, ensure_ascii=False, indent=2)
                print("Saved deliveries_columns.json")

if __name__ == "__main__":
    asyncio.run(main())
