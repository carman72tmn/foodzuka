import asyncio
import httpx
import hashlib
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к приложению
sys.path.append('/app')

async def check_resto():
    from app.core.database import Session, engine
    from app.models.iiko_settings import IikoSettings
    from sqlmodel import select
    
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Settings not found in DB")
            return
            
        resto_url = settings.resto_url
        resto_login = settings.resto_login
        resto_password = settings.resto_password

    if not resto_url or not resto_login or not resto_password:
        print("Resto API credentials incomplete in DB")
        return

    print(f"--- IIKO RESTO API PERMISSION CHECK ---")
    print(f"URL: {resto_url}")
    print(f"Login: {resto_login}")
    
    password_sha1 = hashlib.sha1(resto_password.encode()).hexdigest()
    
    # Normalize URL
    base_url = resto_url.rstrip('/')
    if not base_url.endswith('/api'):
        if base_url.endswith('/resto'):
            base_url = f"{base_url}/api"
        else:
            base_url = f"{base_url}/resto/api"
            
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # 1. Auth
        try:
            auth_res = await client.get(f"{base_url}/auth", params={"login": resto_login, "pass": password_sha1})
            if auth_res.status_code != 200:
                # Try without hashing
                auth_res = await client.get(f"{base_url}/auth", params={"login": resto_login, "pass": resto_password})
                
            if auth_res.status_code != 200:
                print(f"[-] Resto Auth: FAILED ({auth_res.status_code}) - {auth_res.text}")
                return
                
            token = auth_res.text.strip().replace('"', '')
            print("[+] Resto Auth: SUCCESS")
        except Exception as e:
            print(f"[-] Resto Auth: ERROR - {e}")
            return

        # 2. Check Personal Sessions
        now = datetime.now()
        date_from = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = now.strftime("%Y-%m-%d")
        try:
            res = await client.get(f"{base_url}/personalSessions", params={
                "key": token,
                "from": date_from,
                "to": date_to
            })
            if res.status_code == 200:
                print(f"[+] Resto Personal Sessions: SUCCESS")
            else:
                print(f"[-] Resto Personal Sessions: FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            print(f"[-] Resto Personal Sessions: ERROR - {e}")

        # 3. Check Employees
        try:
            res = await client.get(f"{base_url}/employees", params={"key": token})
            if res.status_code == 200:
                print(f"[+] Resto Employees: SUCCESS")
            else:
                print(f"[-] Resto Employees: FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            print(f"[-] Resto Employees: ERROR - {e}")

if __name__ == "__main__":
    asyncio.run(check_resto())
