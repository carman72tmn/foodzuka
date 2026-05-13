import asyncio
import httpx
import hashlib
import json
import os
import sys

# Добавляем путь к backend для импорта настроек
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def get_columns():
    try:
        from app.core.config import settings
        
        # Данные из настроек
        url = settings.IIKO_RESTO_URL or "https://dovezzuka-tyumen.iiko.it"
        login = settings.IIKO_RESTO_LOGIN
        password = settings.IIKO_RESTO_PASSWORD
        
        print(f"Connecting to: {url} as {login}")
        
        base_url = url.rstrip('/')
        if not base_url.endswith('/api'):
            if base_url.endswith('/resto'):
                base_url = f"{base_url}/api"
            else:
                base_url = f"{base_url}/resto/api"
        
        # 1. Auth
        async with httpx.AsyncClient(verify=False) as client:
            password_sha1 = hashlib.sha1(password.encode()).hexdigest()
            auth_url = f"{base_url}/auth"
            resp = await client.get(auth_url, params={"login": login, "pass": password_sha1})
            if resp.status_code != 200:
                resp = await client.get(auth_url, params={"login": login, "pass": password})
            
            if resp.status_code != 200:
                print(f"Auth failed: {resp.status_code} {resp.text}")
                return
            
            token = resp.text.strip().replace('"', '')
            print(f"Auth success, token: {token[:5]}...")
            
            # 2. Get Columns for SALES
            cols_url = f"{base_url}/v2/reports/olap/columns"
            resp = await client.get(cols_url, params={"key": token, "reportType": "SALES"})
            
            if resp.status_code == 200:
                columns = resp.json()
                print("\n=== SALES COLUMNS ===")
                # Фильтруем те, что содержат 'Phone' или 'Guest' или 'Customer'
                for col_id, info in columns.items():
                    name = info.get("name", "")
                    if any(x in col_id or x in name for x in ["Phone", "Guest", "Customer", "Client"]):
                        print(f"{col_id}: {name}")
                
                # Также проверим наличие полей сумм
                print("\n=== AMOUNT/SUM FIELDS ===")
                for col_id, info in columns.items():
                    if "Sum" in col_id or "Amount" in col_id:
                         print(f"{col_id}: {info.get('name')}")
            else:
                print(f"Failed to get SALES columns: {resp.status_code} {resp.text}")

            # 3. Get Columns for DELIVERIES
            resp = await client.get(cols_url, params={"key": token, "reportType": "DELIVERIES"})
            if resp.status_code == 200:
                columns = resp.json()
                print("\n=== DELIVERIES COLUMNS ===")
                for col_id, info in columns.items():
                    name = info.get("name", "")
                    if any(x in col_id or x in name for x in ["Phone", "Guest", "Customer", "Client"]):
                        print(f"{col_id}: {name}")
            else:
                print(f"Failed to get DELIVERIES columns: {resp.status_code} {resp.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_columns())
