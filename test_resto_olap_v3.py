import asyncio
import httpx
import hashlib
import json

async def test_resto_olap_v3():
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

        print("--- Пробуем GET /reports/olap с форматом dd.MM.yyyy ---")
        # Параметры для RMS OLAP (GET)
        # В RMS часто нужно передавать одноименные параметры несколько раз для группировки
        # httpx поддерживает список кортежей для этого
        params = [
            ("key", token),
            ("reportType", "Sales"),
            ("from", "07.04.2026"),
            ("to", "07.04.2026"),
            ("groupRow", "BusinessDate"),
            ("groupRow", "Department"),
            ("agg", "OrderSum"),
            ("agg", "DiscountSum"),
            ("agg", "GuestNum")
        ]
        
        resp = await client.get(f"{base_url}/reports/olap", params=params)
        print(f"GET Status: {resp.status_code}")
        
        if resp.status_code == 200:
            print("Успех! Текст ответа (первые 500 симв):")
            print(resp.text[:500])
            # Пробуем распарсить (иногда RMS возвращает XML или специфичный CSV/JSON)
            try:
                data = resp.json()
                print("JSON получен!")
            except:
                print("Ответ не является JSON.")
        else:
            print(f"Ошибка: {resp.text[:500]}")

if __name__ == "__main__":
    asyncio.run(test_resto_olap_v3())
