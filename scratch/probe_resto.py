import httpx
import asyncio
import hashlib

async def probe():
    url = "https://dovezzuka-tyumen.iiko.it/resto/api"
    login = "superapi"
    password = "superapi" # Assuming password is the same as login based on common patterns, or I should get it from DB
    
    # Actually I should get the password from DB
    from app.core.database import SessionLocal
    from app.models.iiko_settings import IikoSettings
    db = SessionLocal()
    s = db.query(IikoSettings).first()
    password = s.resto_password
    db.close()

    password_sha1 = hashlib.sha1(password.encode()).hexdigest()
    
    async with httpx.AsyncClient(verify=False) as client:
        # Auth
        r = await client.get(f"{url}/auth", params={"login": login, "pass": password_sha1})
        if r.status_code != 200:
            r = await client.get(f"{url}/auth", params={"login": login, "pass": password})
        
        token = r.text.strip().replace('"', '')
        print(f"Token: {token}")
        
        endpoints = [
            "/deliveries/by_date",
            "/deliveryOrders/by_date",
            "/delivery/by_date",
            "/orders/delivery/by_date"
        ]
        
        for ep in endpoints:
            r = await client.get(f"{url}{ep}", params={"from": "2026-04-21", "to": "2026-04-23", "key": token})
            print(f"Endpoint {ep}: {r.status_code}")
            if r.status_code == 200:
                print(f"  Response: {r.text[:200]}")

if __name__ == "__main__":
    asyncio.run(probe())
