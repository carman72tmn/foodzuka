import asyncio
import httpx
import hashlib
import json

async def test_resto_olap_v2():
    url = "https://dovezzuka-tyumen.iiko.it/resto"
    login = "apiuser"
    password = "api12user"
    
    password_sha1 = hashlib.sha1(password.encode()).hexdigest()
    base_url = url.rstrip('/') + "/api"
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # Auth
        auth_response = await client.get(f"{base_url}/auth", params={"login": login, "pass": password_sha1})
        token = auth_response.text.strip().replace('"', '')
        print(f"Token: {token[:5]}...")

        print("--- Пробуем GET /reports/olap ---")
        # В RMS часто параметры передаются через GET
        params = {
            "key": token,
            "reportType": "Sales",
            "from": "2026-04-07",
            "to": "2026-04-07",
            "groupRow": "BusinessDate",
            "groupRow": "Department",
            "agg": "OrderSum"
        }
        resp = await client.get(f"{base_url}/reports/olap", params=params)
        print(f"GET Status: {resp.status_code}")
        print(f"GET Response: {resp.text[:200]}")

        print("\n--- Пробуем POST /reports/olap с иным форматом ---")
        # Некоторые версии хотят 'reportType' как часть URL или иначе
        payload = {
            "reportType": "SALES",
            "groupByRowFields": ["BusinessDate"],
            "aggregateFields": ["OrderSum"]
        }
        resp = await client.post(f"{base_url}/reports/olap", params={"key": token}, json=payload)
        print(f"POST Status: {resp.status_code}")
        
        print("\n--- Пробуем получить список доступных отчетов ---")
        resp = await client.get(f"{base_url}/reports", params={"key": token})
        print(f"Reports list status: {resp.status_code}")
        print(f"Reports list: {resp.text[:500]}")

if __name__ == "__main__":
    asyncio.run(test_resto_olap_v2())
