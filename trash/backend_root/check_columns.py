import asyncio
import httpx
import hashlib
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings

async def test_columns():
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        
    password_sha1 = hashlib.sha1(settings.resto_password.encode()).hexdigest()
    base_url = settings.resto_url.rstrip('/') + "/api"
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        auth = await client.get(f"{base_url}/auth", params={"login": settings.resto_login, "pass": password_sha1})
        token = auth.text.strip().replace('"', '')
        
        # Try both without reportType and with reportType
        resp = await client.get(f"{base_url}/v2/reports/olap/columns", params={"key": token, "reportType": "SALES"})
        print(f"GET columns Status (SALES): {resp.status_code}")
        with open('olap_columns.json', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        print("Columns saved to olap_columns.json")

if __name__ == "__main__":
    asyncio.run(test_columns())
